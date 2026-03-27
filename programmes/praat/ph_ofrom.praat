#praat script: ph_ofrom.praat
# 30.04.2024
# 
# Calls "Align interval" on each valid interval of each tier of a TextGrid.
# Use another script to loop over files/folders.
#
# form:
# - aud_path (sentence): path to audio file 
# - tgd_path (sentence): path to TextGrid file
# - ph_path (sentence):  path for the TextGrid file to output (can overwrite)
# - regT (word):         regex to parse valid tiers (not in label)
# - regI (word):         regex to parse valid intervals (not in label)
# - ch_close (boolean):  whether to close the GUI at script end (console call)
# 
# procedures:
# - 'iterate': reads each tier of a file; extracts each valid tier as 
#              'tmpTGD', processes it with call 'treat_tier' then 
#              merges it with call 'merge_tmp'.
# - 'treat_tier': calls 'treat_part' on each interval of tier 'tmpTGD'
# - 'treat_part': runs 'Align interval' if the label is valid and duration 
#                 >= 0.032s.
# - 'merge_tmp': merges the 'tmpTGD' tier with the final textgrid 'phTGD'
# 
# Error messages:
# - Sound shorter than window length: 			most likely invalid label
# - Cannot change the domain: 					cause not found.
# - Domains not equal: 							cause not found. 
# - Domains Sound & Textgrid should be equal: 	cause not found.
# - Slope constraint: 							cause not found. Still processes?
#   											remains even with 'nocheck'
#
# Note: The script has no form for 'Alignment settings' (see 'treat_part').
# Note: The script has a 'nowarn nocheck noprogress' on 'Align interval'
# Note: Invalid intervals will generate no corresponding interval in new tiers
#       (words/phones). Use another script to fill the gaps.
## 

form: "phonemic alignment"
	sentence: "aud_path",""
	sentence: "tgd_path",""
	sentence: "ph_path",""
	word: "regT","[\[/]"
	word: "regI","[_#@%]"
	boolean: "words",0
endform

procedure treat_part
	if index_regex(tlabel$,regI$) == 0 & (tend-tstart) >= 0.032
		selectObject: tmpTGD,mySound
		nowarn nocheck noprogress Align interval: 1,ni,"French (France)",words,"yes"
	endif
endproc

procedure treat_tier
	selectObject: tmpTGD
	nIntervals = Get number of intervals... 1
	for ni from 1 to nIntervals
		selectObject: tmpTGD
		tstart = Get start point: 1,ni
		tend = Get end point: 1,ni
		tlabel$ = Get label of interval: 1,ni
		call treat_part
	endfor
endproc

procedure merge_tmp
	if ti == 1
		phTGD = tmpTGD
	else
		selectObject: phTGD,tmpTGD
		newTGD = Merge
		selectObject: phTGD,tmpTGD
		Remove
		phTGD = newTGD
	endif
	selectObject: myTGD
endproc

procedure iterate
	writeInfoLine: tgd_path$
	mySound = Read from file... 'aud_path$'
	myTGD = Read from file... 'tgd_path$'
	selectObject: myTGD
	nTiers = Get number of tiers
	for ti from 1 to nTiers
		tname$ = Get tier name: ti
		tmpTGD = Extract one tier... ti
		selectObject: tmpTGD
		if index_regex(tname$,regT$) == 0
			call treat_tier
		endif
		call merge_tmp
	endfor
	selectObject: phTGD
	Write to text file... 'ph_path$'
	selectObject: mySound,myTGD,phTGD
	Remove
endproc

call iterate