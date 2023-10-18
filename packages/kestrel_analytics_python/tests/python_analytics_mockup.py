#!/usr/bin/env python3

import os


def enrich_one_variable(dataframe):
    newattr = ["newval" + str(i) for i in range(dataframe.shape[0])]
    dataframe["x_new_attr"] = newattr

    return dataframe


def html_visualization(dataframe):
    display = "<p>Hello World! -- a Kestrel analytics</p>"

    return display


def enrich_multiple_variables(df1, df2, df3):
    newattr = ["newval_a" + str(i) for i in range(df1.shape[0])]
    df1["x_new_attr"] = newattr

    newattr = ["newval_b" + str(i) for i in range(df2.shape[0])]
    df2["x_new_attr"] = newattr

    newattr = ["newval_c" + str(i) for i in range(df3.shape[0])]
    df3["x_new_attr"] = newattr

    return df1, df2, df3


def enrich_variable_with_arguments(dataframe):
    dataframe["x_new_argx"] = os.environ.get("argx")
    dataframe["x_new_argy"] = os.environ.get("argy")
    dataframe["x_new_argz"] = os.environ.get("argz")

    return dataframe
