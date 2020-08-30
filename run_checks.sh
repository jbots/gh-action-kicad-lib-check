#!/bin/bash

CHECKLIB=$GITHUB_WORKSPACE/kicad-library-utils/schlib/checklib.py
COMPARELIBS=$GITHUB_WORKSPACE/kicad-library-utils/schlib/comparelibs.py
CHECK_KICAD_MOD=$GITHUB_WORKSPACE/kicad-library-utils/pcb/check_kicad_mod.py

RAWOUT=$GITHUB_WORKSPACE/raw_output

NEW=${GITHUB_WORKSPACE}/new
OLD=${GITHUB_WORKSPACE}/old
FOOTPRINTS=${GITHUB_WORKSPACE}/kicad-footprints

files_new=($INPUT_FILES_NEW)
files_modified=($INPUT_FILES_MODIFIED)
files_all=($INPUT_FILES_NEW $INPUT_FILES_MODIFIED)

if [[ -z "${INPUT_RULES_EXCLUDE}" ]]; then
  echo no rules to exclude
else
  EXCLUDE_ARGS="--exclude ${INPUT_RULES_EXCLUDE}"
fi

touch raw_output

echo ..........
echo Search new files for symbols
for file in ${files_new[@]};
do
  echo ${file};
  if [[ $file =~ ${INPUT_SYM_RE} ]]; then
    echo ...found new symbol library ${file}
    python ${CHECKLIB} ${NEW}/${file} -vv --nocolor --footprints ${FOOTPRINTS} ${EXCLUDE_ARGS} >> ${RAWOUT}
  fi
done

echo ..........
echo Search updated files for symbols
for file in ${files_modified[@]};
do
  echo ${file};
  if [[ $file =~ ${INPUT_SYM_RE} ]]; then
    echo ...found updated symbol library $file
    cd $GITHUB_WORKSPACE/kicad-library-utils/schlib # comparelib must be run from here :-/
    python ${COMPARELIBS} --new ${NEW}/${file} --old ${OLD}/${file} --nocolor --check -v --footprints ${FOOTPRINTS} ${EXCLUDE_ARGS} >> ${RAWOUT}
  fi
done

echo ..........
echo Search new and updated files for footprints
for file in ${files_all[@]};
do
  if [[ $file =~ ${INPUT_FP_RE} ]]; then
    echo ...found footprint file ${file}
    python ${CHECK_KICAD_MOD} ${NEW}/${file} -vv --nocolor ${EXCLUDE_ARGS} >> ${RAWOUT}
  fi
done

echo ..........
echo Completed tests

/kicad_to_github_actions.py ${RAWOUT}
if [ $? -ne 0 ]; then exit 1; fi # fail
echo done creating output

# Output as colour html (requires aha)
# aha -f raw_output > output.html
