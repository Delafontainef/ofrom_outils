#praat script: anon_ofrom.praat

#version: [2013-03-06]
#edited [2022-03-18] for OFROM/CFPR use (one file, no verbose, reduced form)
#reedited [2022-07-01] for OFROM/CFPR use (by interval instead of sections)
#                                         (context widened by 2s left-right)
#reedited [2023-07-30] for OFROM/CFPR use (adding 0.5s silence at file end)

#author: Daniel Hirst
#email: daniel.hirst@lpl-aix.fr

#purpose: replace portions of a long sound which are labelled with a key word on the accompanying TextGrid
#		with a hum sound with the same prosodic characteristics as the original sound
#		Original long sound can be mono or stereo, anonymised sound will be same.

#requires: the folder containing the Long_Sounds to be anonymised may be specified or selected with the browser
#		each sound should be accompanied by a TextGrid with the same name

form anonymise_long_sound
	sentence wav_path
	sentence tgd_path
	sentence anon_path
	word output_format WAV
	natural target_tier 1
	word target_label #
	positive section 30
	positive timestep 0.01
	natural minimum_f0 60
	natural maximum_f0 700
	positive scale_intensity 0.98
endform

precision = 50

call treat_sound

procedure treat_sound
	mySound = Open long sound file... 'wav_path$'
	sound_duration = Get total duration
	sampling_frequency = Get sampling frequency
	myTextGrid = Read from file... 'tgd_path$'
	nIntervals = Get number of intervals... target_tier
	iPart = 0
	nTargets = 0
	for intNum from 1 to nIntervals
		iPart = iPart+1
		select myTextGrid
		part_start = Get start point: target_tier, intNum
		part_end = Get end point: target_tier, intNum
		label$ = Get label of interval: 1, intNum
		call treat_part
		endif
	endfor
	
	mySound_part = Create Sound from formula... silence 1 0 0.5 sampling_frequency 0
	Append to existing sound file... 'anon_path$'

	select mySound
	plus myTextGrid
	Remove
endproc

procedure treat_part
	if label$ = target_label$
		word_start = part_start - 2.0
		if word_start < 0.0
			word_start = 0.0
		endif
		word_end = part_end + 2.0
		if word_end > sound_duration
			word_end = sound_duration
		endif
		
		select mySound
		myWord = Extract part... word_start word_end no
		nChannels = Get number of channels
		intensity = Get intensity (dB)
		scaled_intensity = intensity * scale_intensity
		if scaled_intensity != undefined and scaled_intensity > 0
			Scale intensity... scaled_intensity
		endif

		nTargets += 1
		call treat_word
	else
		select mySound
		mySound_part = Extract part... part_start part_end no
	endif
	select mySound_part

	if iPart = 1
		Save as 'output_format$' file... 'anon_path$'
	else
		Append to existing sound file... 'anon_path$'
	endif
	
	anon$ = "anonymised words"
	if nTargets = 1
		anon$ = anon$ - "s"
	endif
endproc

procedure treat_word
	select myWord
	call calculate_min_max_f0

	select myWord
	myScale = Get intensity (dB)
	myPitch = To Pitch... timestep min_f0 max_f0
	myHum_temp = To Sound (hum)
	myHum = Resample... sampling_frequency precision
	select myHum_temp
	Remove

	if nChannels = 2
		myHum_temp = Convert to stereo
		select myHum
		Remove
		myHum = myHum_temp
	endif

	select myWord
	myIntensity = To Intensity... min_f0 timestep no
	myIntensityTier = Down to IntensityTier
	plus myHum
	myNewHum = Multiply... yes
	if myScale != undefined
		Scale intensity... myScale
	endif
	
	select myNewHum
	stime = part_start-word_start
	etime = stime+(part_end-part_start)
	myFinalHum = Extract part... stime etime rectangular 1 no

	select myWord
	plus myPitch
	plus myHum
	plus myIntensity
	plus myIntensityTier
	Remove
	mySound_part = myFinalHum
endproc

procedure calculate_min_max_f0
#  estimate of newMaxF0 as 2.5 * quantile 0.75
#  and newMinF0 as 0.5 * quantile 0.25
#  rounded to higher (resp. lower) 10
	To Pitch... 'timestep' 'minimum_f0' 'maximum_f0'
	.q75 = Get quantile... 0.0 0.0 0.75 Hertz
	.q25 = Get quantile... 0.0 0.0 0.25 Hertz
	max_f0 = 10*ceiling((2.5*.q75)/10)
	min_f0 = 10*floor((0.75*.q25)/10)
	Remove
endproc

#Version history

# [2013-03-07] remove leading or trailing spaces from labels
#			the folder containing the Sounds and TextGrids can be specified or selected with the browser
# [2013-03-06] corrected bug when label to anonymise crosses boundary of section
#			allow output in WAV, AIFF, AIFC, Next/SUN or NIST format
# [2011-03-25] changed extensions ".textGrid" to ".TextGrid"
#			changed max_f0 to 2.5 quantile 75 to allow for more expressive speech
#			resampled buzz to sampling rate of original sound
# [2010:05:24] allowed possibility of stereo long sounds
# [2008:05:25]	first version working.
