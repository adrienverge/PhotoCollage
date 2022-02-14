#	--------▶  2022-02-14 14:24:13 ◀ --------
⭕ git clone https://github.com/adrienverge/PhotoCollage.git
⭕ cd PhotoCollage/
⭕ xgettext --from-code=UTF-8 --keyword=_n:1,2 -o po/photocollage.pot $(find . -name '*.py')
⭕ msginit -l zh_CN.UTF8 -i po/photocollage.pot -o po/zh_CN.po
⭕ geany po/zh_CN.po
⭕ msgfmt -c -v po/zh_CN.po -o po/zh_CN.mo


