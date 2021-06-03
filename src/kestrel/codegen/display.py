from abc import ABC, abstractmethod
from pandas import DataFrame
import json

from kestrel.exceptions import KestrelInternalError


class AbstractDisplay(ABC):
    @abstractmethod
    def to_string(self):
        pass

    @abstractmethod
    def to_html(self):
        pass

    @abstractmethod
    def to_json(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass


class DisplayDataframe(AbstractDisplay):
    def __init__(self, data):
        if isinstance(data, DataFrame):
            self.dataframe = data
        else:
            try:
                self.dataframe = DataFrame(data)
            except ValueError:
                raise KestrelInternalError("invalid input to DisplayDataframe object")

    def to_string(self):
        return self.dataframe.to_string(index=False, na_rep="")

    def to_html(self):
        return self.dataframe.to_html(index=False, na_rep="")

    def to_json(self):
        body = self.dataframe.to_json(orient="records")
        msg = {"display": "dataframe", "data": "<<<BODY>>>"}
        return json.dumps(msg).replace('"<<<BODY>>>"', body)

    def to_dict(self):
        body = self.dataframe.fillna(0).to_dict(orient="records")
        msg = {"display": "dataframe", "data": body}
        return msg


class DisplayBlockSummary(DisplayDataframe):
    def __init__(self, vars_summary, exec_time_sec):
        self.vars_summary = vars_summary
        self.footnotes = []
        self.exec_time_sec = exec_time_sec
        summaries = []
        for summary, footnote in vars_summary:
            summaries.append(summary)
            if footnote and footnote not in self.footnotes:
                self.footnotes.append(footnote)
        super().__init__(summaries)
        self.exec_time_str = self._cal_exec_time(exec_time_sec)

    def to_string(self):
        header = f"[SUMMARY] block executed in {self.exec_time_str}"
        body = super().to_string()
        footer = "\n".join(self.footnotes)
        return "\n".join([header, body, footer])

    def to_html(self):
        header = f"<h4>Block Executed in {self.exec_time_str}</h4>"
        body = self.dataframe.to_html(index=False)
        footer = "<p>" + "<br>".join(self.footnotes) + "</p>"
        return "<div>" + header + body + footer + "</div>"

    def to_json(self):
        data = self.dataframe.to_json(orient="records")
        msg = {
            "display": "execution summary",
            "data": {
                "execution time": self.exec_time_sec,
                "variables updated": "<<<DATA>>>",
                "footnotes": self.footnotes,
            },
        }
        return json.dumps(msg).replace('"<<<DATA>>>"', data)

    def to_dict(self):
        data = self.dataframe.fillna(0).to_dict(orient="records")
        msg = {
            "display": "execution summary",
            "data": {
                "execution time": self.exec_time_sec,
                "variables updated": data,
                "footnotes": self.footnotes,
            },
        }
        return msg

    def _cal_exec_time(self, exec_time_sec):
        hours = exec_time_sec // 3600
        mins = (exec_time_sec // 60) % 60
        secs = exec_time_sec % 60
        x = f"{hours} hours, " if hours else ""
        x = f"{x}{mins} minutes, " if x or mins else ""
        x = f"{x}{secs} seconds" if x or secs else ""
        return x


class DisplayDict(AbstractDisplay):
    def __init__(self, d):
        self.dict = d
        self.dataframe = DataFrame(list(d.items()))

    def to_string(self):
        return self.dataframe.to_string(index=False, header=False, na_rep="")

    def to_html(self):
        clen = self.dataframe[0].str.len().max()
        return self.dataframe.to_html(
            index=False, header=False, na_rep="", col_space=[f"{clen}em", "1em"]
        )

    def to_json(self):
        msg = {"display": "dict", "data": self.dict}
        return json.dumps(msg)

    def to_dict(self):
        msg = {"display": "dict", "data": self.dict}
        return msg


class DisplayHtml(AbstractDisplay):
    def __init__(self, html):
        self.html = html

    def to_string(self):
        return self.html

    def to_html(self):
        return self.html

    def to_json(self):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError
