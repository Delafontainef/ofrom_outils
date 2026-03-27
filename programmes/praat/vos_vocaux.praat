#### Praat script 'vos_vocaux'
#
# Creates a TextGrid based on a soundfile.
#
####

form: "anonymise_ofrom"
	sentence: "wav_path",""
	sentence: "tgd_path",""
	sentence: "tier_name","ortho"
endform

procedure new_tgd
	#### Creates a TextGrid corresponding to the soundfile
	wav = Read from file... 'wav_path$'
	sound_duration = Get total duration
	tgd = To TextGrid... 'tier_name$' ''
	if tgd_path$ = ""
		tgd_path$ = "ortho.TextGrid"
	endif
	Save as text file... 'tgd_path$'
	
	selectObject: wav,tgd
	Remove
endproc

call new_tgd