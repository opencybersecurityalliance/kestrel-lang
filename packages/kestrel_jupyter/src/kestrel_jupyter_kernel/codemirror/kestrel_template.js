(function(mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function(CodeMirror) {
  "use strict";

  CodeMirror.defineMode("kestrel", function() {

    function switchState(source, setState, f) {
      setState(f);
      return f(source, setState);
    }

    var smallRE = /[a-z_]/;
    var largeRE = /[A-Z]/;
    var digitRE = /[0-9]/;
    var hexitRE = /[0-9A-Fa-f]/;
    var octitRE = /[0-7]/;
    var idRE = /[a-z_A-Z0-9\']/;
    var typeRE = /[a-zA-Z0-9-]/;
    var symbolRE = /[-!#$%&*+.\/<=>?@\\^|~:]/;
    var specialRE = /[(),;[\]`{}]/;
    var whiteCharRE = /[ \t\v\f]/; // newlines are handled in tokenizer
    var isoTimestamp = /[0-9:.\-TZ]/;

    function normal() {
      return function (source, setState) {
        if (source.eatWhile(whiteCharRE)) {
          return null;
        }

        var ch = source.next();

        if (ch == '#') {
          source.skipToEnd();
          return "comment";
        }

        if (ch == '\'') {
          return switchState(source, setState, stringLiteral);
        }

        if (ch == 't') {
          if (source.eat('\'')) {
            source.eatWhile(isoTimestamp);
            if (source.eat('\'')) {
              return "string-2";
            }
          }
        }

        if (typeRE.test(source)) {
          source.eatWhile(typeRE);
          return "type";
        }

        if (largeRE.test(ch)) {
          source.eatWhile(idRE);
          return "error";
        }

        if (smallRE.test(ch)) {
          source.eatWhile(idRE);
          return "variable";
        }

        if (digitRE.test(ch)) {
          if (ch == '0') {
            if (source.eat(/[xX]/)) {
              source.eatWhile(hexitRE); // should require at least 1
              return "integer";
            }
            if (source.eat(/[oO]/)) {
              source.eatWhile(octitRE); // should require at least 1
              return "number";
            }
          }
          source.eatWhile(digitRE);
          var t = "number";
          if (source.eat('.')) {
            t = "number";
            source.eatWhile(digitRE); // should require at least 1
          }
          if (source.eat(/[eE]/)) {
            t = "number";
            source.eat(/[-+]/);
            source.eatWhile(digitRE); // should require at least 1
          }
          return t;
        }

        if (symbolRE.test(ch)) {
          if (ch == '#') {
            source.skipToEnd();
            return "comment";
          }
        }

        return "error";
      }
    }

    function stringLiteral(source, setState) {
      while (!source.eol()) {
        var ch = source.next();
        if (ch == '\'') {
          setState(normal());
          return "string";
        }
        // escape handling: need to test correctness
        //if (ch == '\\') {
        //  if (source.eat('\'')) source.next();
        //}
      }
      setState(normal());
      return "error";
    }

    var wellKnownWords = (function() {
      var wkw = {};

      var keywords = <<<KEYWORDS>>>;

      for (var i = keywords.length; i--;)
        wkw[keywords[i]] = "keyword";

      var ops = ["IN", "NOT", "LIKE", "MATCHES", "ISSUBSET", "in", "not", "like", "matches", "isubset", "=", "!=", "<", ">", "<=", ">=",];

      for (var i = ops.length; i--;)
        wkw[ops[i]] = "operator";

      return wkw;
    })();

    return {
      startState: function ()  { return { f: normal() }; },
      copyState:  function (s) { return { f: s.f }; },

      token: function(stream, state) {
        var t = state.f(stream, function(s) { state.f = s; });
        var w = stream.current();
        return (wellKnownWords.hasOwnProperty(w)) ? wellKnownWords[w] : t;
      }
    };

  });

  CodeMirror.defineMIME("text/x-kestrel", "kestrel");
});
