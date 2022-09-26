#!/usr/bin/env bash

# https://www.npmjs.com/package/svgexport

for svgfile in *.svg
do
    pngfile="${svgfile%.svg}.png"
    svgexport $svgfile $pngfile 100% 4x
done
