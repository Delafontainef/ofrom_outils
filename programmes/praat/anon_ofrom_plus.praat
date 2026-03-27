#praat script: anon_ofrom_plus.praat

#original version [2013-03-06]
#modified version [2025-09-25] for OFROM+ use

#author: Daniel Hirst
#email: daniel.hirst@lpl-aix.fr

#purpose: replace portions of a long sound which are labelled with a key word on the accompanying TextGrid
#		with a hum sound with the same prosodic characteristics as the original sound
#		Original long sound can be mono or stereo, anonymised sound will be same.

#requires: the folder containing the Long_Sounds to be anonymised may be specified or selected with the browser
#		each sound should be accompanied by a TextGrid with the same name

## /!\ modified form, 'anon_path' basename should have no extension
## no more 'target_tier'

form: "anonymise_ofrom"
	sentence: "wav_path",""
	sentence: "tgd_path",""
	sentence: "anon_path",""
	word: "output_format","WAV"
	word: "target_label","#"
    word: "save_directly","yes"
	positive: "timestep", "0.01"
	natural: "minimum_f0", "60"
	natural: "maximum_f0", "700"
	positive: "scale_intensity", "0.98"
endform

precision = 50
Text writing preferences: "UTF-8"

    #### Reduce sound to mono ####
    #----------------------------#

procedure to_mono
    #### reduces sound to mono
    selectObject: mySound
    newSound = Convert to mono
    selectObject: mySound
    Remove
    mySound = newSound
endproc

    #### Ensures TextGrid starts at 0. ####
    #-------------------------------------#
    
procedure check_start
    #### cut wav/tgd to [0., end]
    selectObject: myTGD
    start = Get start time
    end = Get end time
    tmpTGD = myTGD
    myTGD = Extract part: 0., end, "no"
    
    selectObject: mySound
    tmpSound = mySound
	mySound = Extract part: start, end, "rectangular", 1, "no"
    selectObject: mySound
    sound_duration = Get total duration
    
    selectObject: tmpTGD, tmpSound
    Remove
endproc

	#### Remove start/end anonymized parts ####
	#-----------------------------------------#

procedure cut_file
	#### Removes first/last interval if all segments are "target_label"
	check_start = 1
	old_time_start = -1.
	check_end = 1
	old_time_end = -1.
	selectObject: myTGD
	nTiers = Get number of tiers
	for ti from 1 to nTiers
		nIntervals = Get number of intervals... ti
		label_start$ = Get label of interval: ti,1
		time_start = Get end point: ti,1
		label_end$ = Get label of interval: ti,nIntervals
		time_end = Get start point: ti,nIntervals
		if not label_start$ = target_label$
			check_start = 0
		endif
		if old_time_start < time_start
			old_time_start = time_start
		endif
		if not label_end$ = target_label$
			check_end = 0
		endif
		if old_time_end < 0. or old_time_end > time_end
			old_time_end = time_end
		endif
	endfor
	if check_start or check_end
		if not check_start
			old_time_start = 0.
		endif
		if not check_end
			old_time_end = sound_duration
		endif
		selectObject: myTGD
		newTGD = Extract part: old_time_start, old_time_end,0
		selectObject: mySound
		newSound = Extract part: old_time_start, old_time_end,"rectangular",1.0,0
		
		selectObject: myTGD,mySound
		Remove
		myTGD = newTGD
		mySound = newSound
	endif
    
    selectObject: myTGD
    Save as text file: anon_tgd_path$
endproc

	#### Create and fill 'anonTGD' ####
	#---------------------------------#

procedure select_interval
	#### selects an interval to work with
	selectObject: myTGD
	for ti from 1 to nTiers
		if tind#[ti] <= tmax#[ti]
			ch_while = 1
			tmp_start = Get start point: ti, tind#[ti]
			tmp_end = Get end point: ti, tind#[ti]
			if part_start < 0 or tmp_start < part_start
				oti = ti
				part_start = tmp_start
				part_end = tmp_end
			endif
		endif
	endfor
endproc

procedure add_interval
	#### add the interval to 'anonTGD' if conditions are met
	if label$ = target_label$
		if ch_anon = 1 and part_end > end
			end = part_end
		elsif ch_anon = 0
			start = part_start
			end = part_end
			ch_anon = 1
		endif
	elsif ch_anon = 1 and part_start >= end
		ch_anon = 0
		selectObject: anonTGD
		if start > ch_time
			anon_nint = anon_nint + 1
			Insert boundary: 1, start
            ch_time = start
		endif
		Set interval text: 1, anon_nint, target_label$
		if end > ch_time and end < sound_duration
			anon_nint = anon_nint + 1
			Insert boundary: 1, end
            ch_time = end
		endif
		selectObject: myTGD
	endif
endproc

procedure fill_anon_tier
	#### builds the 'anonTGD'
	anonTGD = Create TextGrid... 0. sound_duration "anon"
	selectObject: myTGD
	nTiers = Get number of tiers
	tind# = zero# (nTiers)
	tmax# = zero# (nTiers)
	for ti from 1 to nTiers
		tmax#[ti] = Get number of intervals... ti
		tind#[ti] = tind#[ti] + 1
	endfor
	
	start = -1.
	end = -1.
	anon_nint = 1
	ch_anon = 0
	ch_while = 1
    ch_time = 0.
	while ch_while
		oti = -1
		part_start = -1.
		part_end = -1.
		call select_interval
		if oti < 0
			ch_while = 0
		else
			label$ = Get label of interval: oti, tind#[oti]
			call add_interval
			tind#[oti] = tind#[oti] + 1
		endif
	endwhile
		# last loop (should not happen, see 'cut_file')
	if ch_anon
		selectObject: anonTGD
		anon_nint = anon_nint + 1
		Insert boundary: 1, start
		Set interval text: 1, anon_nint, target_label$
	endif
endproc

	#### Anonymization proper (Hirst 2013) ####
	#-----------------------------------------#

procedure calculate_min_max_f0
	#### Used in 'treat_word' to get 'min_f0', 'max_f0'
	# estimate of newMaxF0 as 2.5 * quantile 0.75
	# and newMinF0 as 0.5 * quantile 0.25
	# rounded to higher (resp. lower) 10
	To Pitch... 'timestep' 'minimum_f0' 'maximum_f0'
	.q75 = Get quantile... 0.0 0.0 0.75 Hertz
	.q25 = Get quantile... 0.0 0.0 0.25 Hertz
	max_f0 = 10*ceiling((2.5*.q75)/10)
	min_f0 = 10*floor((0.75*.q25)/10)
	Remove
endproc

procedure treat_word
	#### Generates the hum (for anonymization)
	select myWord
	call calculate_min_max_f0

	selectObject: myWord
	myScale = Get intensity (dB)
	myPitch = To Pitch... timestep min_f0 max_f0
	myHum = To Sound (hum)
	if nChannels = 2
        newHum = Convert to stereo
        selectObject: myHum
        Remove
        myHum = newHum
	endif
	
	myHum = Resample... sampling_frequency precision
	selectObject: myPitch
	Remove

	selectObject: myWord
	myIntensity = To Intensity... min_f0 timestep no
	myIntensityTier = Down to IntensityTier
	plus myHum
	myNewHum = Multiply... yes
	if myScale != undefined
		Scale intensity... myScale
	endif
	
	selectObject: myNewHum
	stime = part_start-word_start
	etime = stime+(part_end-part_start)
	myFinalHum = Extract part: stime, etime, "rectangular", 1, "no"

	selectObject: myWord, myHum, myIntensity, myIntensityTier, myNewHum
	Remove
	mySound_part = myFinalHum
endproc

procedure save_part
    #### Handles saving the part
    if save_directly$ = "no"
        selectObject: newSound, mySound_part
        tmpSound = newSound
        newSound = Concatenate
        selectObject: tmpSound, mySound_part
    else
        selectObject: mySound_part
        if ni = 1
            Save as 'output_format$' file... 'anon_wav_path$'
        else
            Append to existing sound file... 'anon_wav_path$'
        endif
    endif
    Remove
endproc

procedure treat_part
	#### Anonymizes interval if need be, appends hum/copy to final file
	if label$ = target_label$
		word_start = part_start - 2.0
		if word_start < 0.0
			word_start = 0.0
		endif
		word_end = part_end + 2.0
		if word_end > sound_duration
			word_end = sound_duration
		endif
		
		selectObject: mySound
		myWord = Extract part: word_start, word_end, "rectangular", 1, "no"
		nChannels = Get number of channels
		intensity = Get intensity (dB)
		scaled_intensity = intensity * scale_intensity
		if scaled_intensity != undefined and scaled_intensity > 0
			Scale intensity... scaled_intensity
		endif

		call treat_word
	else
		selectObject: mySound
		mySound_part = Extract part: part_start, part_end, "rectangular", 1, "no"
	endif
	
	call save_part
endproc

procedure newsound
    #### Creates an "empty" new sound object to be appended
    selectObject: mySound
    sampling_frequency = Get sampling frequency
    newSound = Create Sound from formula: "silence", 1, 0.0, 0.0001, sampling_frequency, "0"
endproc

procedure save_sound
    #### Handles saving the whole sound
    if save_directly$ = "no"
        selectObject: newSound
        Save as 'output_format$' file... 'anon_wav_path$'
        selectObject: newSound, anonTGD
    else
        selectObject: anonTGD
    endif
	Remove
endproc

procedure anonymize
	#### Gets over each interval of 'anonTGD' and calls 'treat_part'
    if save_directly$ = "no"
        call newsound
    endif
    
    selectObject: anonTGD
	nIntervals = Get number of intervals... 1
	for ni from 1 to nIntervals
		selectObject: anonTGD
		part_start = Get start point: 1, ni
		part_end = Get end point: 1, ni
		label$ = Get label of interval: 1, ni
		call treat_part
		endif
	endfor
    
    call save_sound
endproc

	#### Ensure sound length ####
	#---------------------------#
	
procedure check_duration_length
	#### Checks duration length (of anonymized audio) and adds if need be
	#### (should cut textgrid instead...)
	anonSound = Read from file: anon_wav_path$
	sound_duration = Get total duration
    sampling_frequency = Get sampling frequency
    nChannels = Get number of channels
	selectObject: myTGD
	tgd_duration = Get total duration
	diff = tgd_duration - sound_duration
	if diff > 0
		diff = diff+0.001
		mySound_part = Create Sound from formula: "silence", nChannels, 0, diff, sampling_frequency, "0"
        Append to existing sound file: anon_wav_path$
		selectObject: mySound_part
		Remove
	endif
	
	selectObject: anonSound
	Remove
endproc

procedure add_silence
	#### Adds 0.1s at the end of the sound (for safety)
    anonSound = Read from file: anon_wav_path$
    nChannels = Get number of channels
	mySound_part = Create Sound from formula... silence nChannels 0 0.1 sampling_frequency 0
	Append to existing sound file... 'anon_wav_path$'
	selectObject: mySound_part
	Remove
endproc

	#### Main procedure ####
	#----------------------#

procedure treat_sound
	#### Main
	anon_wav_path$ = anon_path$+".wav"
	anon_tgd_path$ = anon_path$+".TextGrid"
	mySound = Read from file... 'wav_path$'
	sound_duration = Get total duration
	sampling_frequency = Get sampling frequency
	myTGD = Read from file... 'tgd_path$'
	
    call to_mono
    call check_start
	call cut_file
	call fill_anon_tier
	call anonymize
	call check_duration_length
	call add_silence
	
	selectObject: mySound,myTGD
	Remove
endproc

call treat_sound

#### Version history
# [2013-03-07] remove leading or trailing spaces from labels
#			the folder containing the Sounds and TextGrids can be specified or selected with the browser
# [2013-03-06] corrected bug when label to anonymise crosses boundary of section
#			allow output in WAV, AIFF, AIFC, Next/SUN or NIST format
# [2011-03-25] changed extensions ".textGrid" to ".TextGrid"
#			changed max_f0 to 2.5 quantile 75 to allow for more expressive speech
#			resampled buzz to sampling rate of original sound
# [2010-05-24] allowed possibility of stereo long sounds
# [2008-05-25] first version working.
# [2013-03-06]
# [2022-03-18] for OFROM/CFPR use (one file, no verbose, reduced form)
# [2022-07-01] for OFROM/CFPR use (by interval instead of sections)
#                                 (context widened by 2s left-right)
# [2023-07-30] for OFROM/CFPR use (adding 0.5s silence at file end)
# [2024-04-30] for OFROM+ use (cut_file, fill_anon_tier)
# [2024-05-07] for OFROM+ use (check_duration_length)
# [2025-09-25] for OFROM+ use (to_mono)