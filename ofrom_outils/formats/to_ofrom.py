"""18/03/2022
Export for the OFROM corpus.

Note: no matter the import, 'textgrid_url' will always have '.TextGrid'.
Note: The speaker's name can't be 'trans' (reserved key).
Note: metadata keys are hard-coded ('l_sound/l_spk','communication/speakerID')
Note: 'l_audio' limits the audio formats (see _getInput()).
Note: special symbols are in 'l_syms' (see '_writeSegs()').
"""

import hashlib
import html
import os

from corflow.Transcription import Corpus, Transcription

# Variables
l_syms = ["#", "@", "_"]


class Stats:
    def __init__(self, l_tiers):
        self.d_spk = {'trans':
                          {'TimeTotalSample': 0.0, 'TimeSingleSpeaker': 0.0,
                           'TimeOverlap': 0.0, 'TimeGap': 0.0,
                           'RatioSingleSpeaker': -1., 'RatioOverlap': -1.,
                           'RatioGap': -1., 'GapDurations_Median': -1.,
                           'GapDurations_Q1': -1., 'GapDurations_Q3': -1.,
                           'TurnChangesCount': 0, 'TurnChangesCount_Gap': 0,
                           'TurnChangesCount_Overlap': 0,
                           'TurnChangesRate': -1.,
                           'TurnChangesRate_Gap': -1.,
                           'TurnChangesRate_Overlap': -1.}}
        self.gaps = []
        self.sil, self.fil = [], []
        self.cont = ""
        self.wc = 0
        self.setup(l_tiers)

    def setup(self, l_tiers):
        for tier in l_tiers:
            self.d_spk[tier.name] = \
                {'speakerID': tier.name, 'TimeSpeech': 0.0,
                 'TimeArticulation': 0.0,
                 'TimeArticulation_Alone': 0.0, 'TimeArticulation_Overlap': 0.0,
                 'TimeArticulation_Overlap_Continue': 0.0,
                 'TimeArticulation_Overlap_TurnChange': 0.0,
                 'TimeSilentPause': 0.0, 'TimeFilledPause': 0.0,
                 'RatioArticulation': -1., 'RatioArticulation_Alone': -1.,
                 'RatioArticulation_Overlap': -1.,
                 'RatioArticulation_Overlap_Continue': -1.,
                 'RatioArticulation_Overlap_TurnChange': -1.,
                 'RatioSilentPause': -1., 'RatioFilledPause': -1.,
                 'NumTokens': 0, 'NumSyllables': 0, 'NumSilentPauses': 0,
                 'NumFilledPauses': 0, 'SpeechRate': -1.,
                 'SilentPauseRate': -1.,
                 'FilledPauseRate': -1., 'ArticulationRate': -1.,
                 'PauseDur_SIL_Median': -1., 'PauseDur_SIL_Q1': -1.,
                 'PauseDur_SIL_Q3': -1., 'PauseDur_FIL_Median': -1.,
                 'PauseDur_FIL_Q1': -1., 'PauseDur_FIL_Q3': -1.,
                 'TurnDuration_Time_Mean': -1., 'TurnDuration_Syll_Mean': -1.,
                 'TurnDuration_Token_Mean': -1.,
                 'IntersyllabicInterval_Mean': -1.,
                 'IntersyllabicInterval_StDev': -1.}

    def check_overlap(self, l_tiers):
        """Calcultes overlap durations across all tiers...
        Must include continue/turn change..."""

        def sep_over(atier, aseg):
            dur = aseg.end - aseg.start
            ach, aodur = False, 0.0
            l_over = seg.meta('overlap', "tech", ch_list=True)
            for sa, ea in l_over:
                aodur = aodur + (ea - sa)
            ach = True if (l_over and l_over[-1][1] == aseg.end) else False
            if (aseg.content not in l_syms) and ("%" not in aseg.content):
                self.d_spk[atier.name]['TimeArticulation_Overlap'] += aodur
                self.d_spk[atier.name]['TimeArticulation_Alone'] += (
                            dur - aodur)
            return ach, aodur

        if not l_tiers:
            return
        tr = l_tiers[0].struct
        l_bounds = tr.meta("timetable", "tech")
        if not l_bounds:
            l_bounds = tr.timetable(l_tiers)
            tr.setMeta("timetable", l_bounds, "tech")
        for a in range(1, len(l_bounds)):  # overlaps per segment
            s, e = l_bounds[a - 1], l_bounds[a]
            d_segs = {}
            for tier in l_tiers:
                seg = tier.getTime(s, tier)
                if seg.meta("type", "tech").lower() == "text":
                    d_segs[tier] = seg
            k, kk = 'pause', 'TimeGap'
            if len(d_segs) == 1:
                k, kk = 'alone', 'TimeSingleSpeaker'
            elif len(d_segs) > 1:
                k, kk = 'overlap', 'TimeOverlap'
            else:
                self.gaps.append(e - s)
            self.d_spk['trans'][kk] += e - s
            for tier, seg in d_segs.items():
                seg.setMeta(k, (s, e), "tech", -1)
        for tier in l_tiers:  # fill (+ TurnChange)
            if len(tier) == 1:
                seg = tier.elem[0]
                sep_over(tier, seg)
                continue
            for a in range(0, len(tier)):
                seg = tier.elem[a]
                sep_over(tier, seg)

    def add_words(self, spk, seg, cont, lc):
        self.cont += cont
        self.wc += lc
        dur = seg.end - seg.start
        self.d_spk[spk]['TimeSpeech'] += dur
        self.d_spk[spk]['NumTokens'] += lc
        self.d_spk[spk]['NumSyllables'] += lc
        ak, kk = 'TimeArticulation', ''
        if seg.content in l_syms:
            ak = 'TimeSilentPause'
            kk = 'NumSilentPauses'
            self.sil.append(dur)
        elif "%" in seg.content:
            ak = 'TimeFilledPause'
            kk = 'NumFilledPauses'
            self.fil.append(dur)
        self.d_spk[spk][ak] += dur
        if kk:
            self.d_spk[spk][kk] += 1

    def check_stats(self):
        def no_zero(t1, t2):
            res = t1 / t2 if (t2 != 0.) else -1.
            return res

            # Trans

        d_vals = self.d_spk['trans']
        d_vals['TimeTotalSample'] = (d_vals['TimeSingleSpeaker'] +
                                     d_vals['TimeOverlap'] +
                                     d_vals['TimeGap'])
        d_vals['RatioSingleSpeaker'] = no_zero(d_vals['TimeSingleSpeaker'],
                                               d_vals['TimeTotalSample'])
        d_vals['RatioOverlap'] = no_zero(d_vals['TimeOverlap'],
                                         d_vals['TimeTotalSample'])
        d_vals['RatioGap'] = no_zero(d_vals['TimeGap'],
                                     d_vals['TimeTotalSample'])
        self.gaps.sort()
        lg = len(self.gaps)
        if self.gaps:
            d_vals['GapDurations_Median'] = self.gaps[lg // 2]
            d_vals['GapDurations_Q1'] = self.gaps[lg // 4]
            d_vals['GapDurations_Q3'] = self.gaps[(3 * lg) // 4]
            # Speakers
        for spk, d_vals in self.d_spk.items():
            if spk == "trans":
                continue
                # Fill missing stats
            d_vals['RatioArticulation'] = no_zero(d_vals['TimeArticulation'],
                                                  d_vals['TimeSpeech'])
            d_vals['RatioArticulation_Alone'] = \
                no_zero(d_vals['TimeArticulation_Alone'], d_vals['TimeSpeech'])
            d_vals['RatioArticulation_Overlap'] = \
                no_zero(d_vals['TimeArticulation_Overlap']
                        , d_vals['TimeSpeech'])
            d_vals['RatioSilentPause'] = \
                no_zero(d_vals['TimeSilentPause'], d_vals['TimeSpeech'])
            d_vals['RatioFilledPause'] = \
                no_zero(d_vals['TimeFilledPause'], d_vals['TimeSpeech'])
            d_vals['SpeechRate'] = \
                no_zero(d_vals['NumSyllables'], d_vals['TimeSpeech'])
            d_vals['SilentPauseRate'] = \
                no_zero(d_vals['NumSilentPauses'], d_vals['TimeSpeech'])
            d_vals['FilledPauseRate'] = \
                no_zero(d_vals['NumFilledPauses'], d_vals['TimeSpeech'])
            d_vals['ArticulationRate'] = \
                no_zero(d_vals['NumSyllables'], d_vals['TimeArticulation'])
            self.fil.sort()
            self.sil.sort()
            lf, ls = len(self.fil), len(self.sil)
            if self.sil:
                d_vals['PauseDur_SIL_Median'] = self.sil[ls // 2]
                d_vals['PauseDur_SIL_Q1'] = self.sil[ls // 4]
                d_vals['PauseDur_SIL_Q3'] = self.sil[(3 * ls) // 4]
            if self.fil:
                d_vals['PauseDur_FIL_Median'] = self.fil[lf // 2]
                d_vals['PauseDur_FIL_Q1'] = self.fil[lf // 4]
                d_vals['PauseDur_FIL_Q3'] = self.fil[(3 * lf) // 4]

    # Technical functions


def _ch_encoding(trans, encoding):
    """Seeks encoding (default "utf_8")."""

    if not encoding:  # No user-defined encoding
        return trans.meta('encoding', 'tech', empty="utf_8")  # Check meta
    else:  # User-defined
        return encoding

    # Writing functions


def _set_trans(trans):
    """Restructure, parent and add types."""

    def set_type(tiera):  # sets the 'type' parameter per segment
        """Give 'type' parameter to first main tier."""
        for seg in tiera:
            # Check the segment itself
            if seg.content in l_syms:
                seg.setMeta("type", "PAUSE", "tech")
                continue
            else:
                seg.setMeta("type", "TEXT", "tech")

    l_tiers = []
    # Store main tiers in 'l_tiers'
    trans.setBounds()
    for tier in trans:
        if "[" in tier.name:  # Only process top(speaker) tiers
            continue
        tier.setMeta("index", 0, "tech")  # indexes for writing tables
        l_tiers.append(tier)
        # Set 'type' parameter (pause/text)
    for tier in l_tiers:
        set_type(tier)
    return l_tiers


def _write_segs(l_tiers, stats):
    """Writes SOUNDSEGMENTS"""

    def add_args(tag, l_args):
        """Writes a tag for SOUNDSEGMENT,TOKMIN or TOKMWU."""
        txt = "\t\t\t<" + tag
        for tpl in l_args:
            k, v = tpl[0], tpl[1]
            v = html.escape(str(v))
            txt = txt + " {}=\"{}\"".format(k, v)
        txt = txt + " />\n"
        return txt

    def iter_args(tiera, i_sega, i_sub, d_csegsa, anno="min"):
        """Writes TOKMIN/TOKMWU segment, partly."""
        tr = tiera.struct
        l_pos = d_csegsa.get(tr.getName(tiera.name + "[pos_" + anno + "]"))
        l_tok = d_csegsa.get(tr.getName(tiera.name + "[tok_" + anno + "]"))
        l_lem = d_csegsa.get(tr.getName(tiera.name + "[lemma]"))
        if not l_pos:
            return
        for aa in range(len(l_pos)):
            pos_seg, tok_seg, lem_seg = l_pos[aa], l_tok[aa], l_lem[aa]
            sa = "{:.04f}".format(pos_seg.start)
            ea = "{:.04f}".format(pos_seg.end)
            l_args = [("id", str(i_sub)), ("speaker_id", tiera.name),
                      ("soundsegment_id", str(i_sega)),
                      ("interval_nr", pos_seg.index()), ("tmin", sa),
                      ("tmax", ea),
                      ("text", tok_seg.content),
                      ("pos_" + anno, pos_seg.content)]
            i_sub += 1
            yield tok_seg, i_sub, l_args, lem_seg

    def write_min(tmina, conta, tiera, sega, d_csegsa, i_sega, i_mina):
        """Writes the 'tokmin' part."""
        lca = 0
        for min_seg, i_mina, l_args, lem_seg in iter_args(
                tiera, sega, i_sega, i_mina, d_csegsa):
            if min_seg.content not in l_syms:
                lca += 1
            lem = html.escape(lem_seg.content)
            if lem.count("|") > 3:
                l_lem = lem.split("|")
                l_args = l_args + [("pos_ext_min", l_lem[1]),
                                   ("disfluency", l_lem[3]),
                                   ("lemma", l_lem[0])]
            else:
                l_args = l_args + [("pos_ext_min", ""), ("disfluency", ""),
                                   ("lemma", lem)]
            tmina = tmina + add_args("tokmin", l_args)
            conta = conta + " " + html.escape(min_seg.content)
        return tmina, i_mina, conta, lca

    def write_mwu(tmwua, tiera, d_csegsa, i_sega, i_mwua):
        """Writes the 'tokmwu' part."""
        for mwu_seg, i_mwua, l_args, lem_seg in iter_args(
                tiera, i_sega, i_mwua, d_csegsa, anno="mwu"):
            lem = html.escape(lem_seg.content)
            if "|" in lem:
                l_lem = lem.split("|")
                l_args = l_args + [("pos_ext_mwu", l_lem[2]),
                                   ("discourse", l_lem[4])]
            else:
                l_args = l_args + [("pos_ext_mwu", ""), ("discourse", "")]
            tmwua = tmwua + add_args("tokmwu", l_args)
        return tmwua, i_mwua

    def write_seg(tiera, sega, i_sega, i_nra, lca):
        """Writes the 'soundsegment' part."""
        sa = "{:.04f}".format(sega.start)
        ea = "{:.04f}".format(sega.end)
        d = "{:.04f}".format(sega.end - sega.start)
        l_args = [("id", str(i_sega)), ("speaker_id", tiera.name),
                  ("name", tiera.name + "_" + str(i_sega)),
                  ("interval_nr", i_nra),
                  ("duration", d), ("word_count", lca), ("tmin", sa),
                  ("tmax", ea),
                  ("text", html.escape(sega.content)),
                  ("type", sega.meta("type", "tech"))]
        return add_args("soundsegment", l_args)

        # Variables

    tseg = "\t<annotation>\n\t\t<table_soundsegment>\n"
    tmin = "\t\t<table_tok_min>\n"
    tmwu = "\t\t<table_tok_mwu>\n"
    i_seg, i_min, i_mwu = 0, 0, 0
    while True:  # Like 'iterTime()'
        # Get segments
        l_segs = []
        for tier in l_tiers:  # Get each tier's segment
            pos = tier.meta("index", "tech")
            if pos < 0:  # end of tier
                l_segs.append(None)
                continue
            l_segs.append(tier.elem[pos])
            # Select segment
        pos, seg = -1, None
        for a, s in enumerate(l_segs):  # Pick one
            if not s:
                continue
            elif not seg or (s.start < seg.start):
                seg = s
        if not seg:  # End of loop
            break
            # Write
        tier = seg.struct
        i_nr = tier.meta("index", "tech")
        d_csegs = seg._childDict(seg.children())
        tmin, i_min, cont, lc = write_min(tmin, "", tier, seg, d_csegs,
                                          i_seg, i_min)
        tmwu, i_mwu = write_mwu(tmwu, tier, d_csegs, i_seg, i_mwu)
        tseg = tseg + write_seg(tier, seg, i_seg, i_nr, lc)
        stats.add_words(tier.name, seg, cont, lc)
        # Increment
        i_seg += 1
        i_nr = i_nr + 1 if i_nr + 1 < len(tier) else -1
        tier.setMeta("index", i_nr, "tech")
        # Close and combine
    tseg = tseg + "\t\t</table_soundsegment>\n"
    tmin = tmin + "\t\t</table_tok_min>\n"
    tmwu = tmwu + "\t\t</table_tok_mwu>\n"
    tseg = tseg + tmwu + tmin + "\t</annotation>\n"
    stats.cont = stats.cont.strip()
    return tseg, stats


def _write_metadata(trans, enc, div="speakers"):
    """Writes SOUND/SPEAKERS"""

    def write_trans_arg(txta, d_d):
        """Arguments in transcription metadata."""
        for k, nk in d_d.items():
            v = trans.meta(k)
            v = 'NR' if not v else v
            txta = txta + " {}=\"{}\"".format(nk, html.escape(str(v)))
        return txta

    def write_spk_arg(txta, d_d, d_nd):
        """Arguments in speaker metadata."""
        for k, nk in d_d.items():
            v = d_nd.get(k)
            v = 'NR' if not v else v
            txta = txta + " {}=\"{}\"".format(nk, html.escape(str(v)))
        return txta

    def write_com(txta, taba):
        """<communication> tag."""

        def fix_reviseur():
            """Only two fields in XML, 4 in Excel file."""
            # reviseur_1 reviseur_2 reviseur_1_date reviseur_2_date
            # revised_by revision_date
            revised_by, revision_date, ch_date = "", "", -1
            for k, v in trans.metadata['omni'].items():
                v = v[0] if v else ""
                if "reviseur" not in k:
                    continue
                l_v = v.split(";") if ";" in v else [v]
                if "date" in k:
                    ch = int(k.split("_")[1])
                    if ch > ch_date:
                        revision_date = l_v[-1]
                        ch_date = ch
                else:
                    for nv in l_v:
                        nv = nv.replace(",", "")
                        revised_by = revised_by + " , " + nv
            if revised_by:
                main, last = revised_by[2:].rsplit(",", 1)
                last = last.strip()
                revised_by = main + " & " + last
            return revised_by, revision_date

            # Variables

        audio = trans.meta("audio_path")
        if audio:
            ndir, f_audio = os.path.split(audio)
            a_fi, a_ext = os.path.splitext(f_audio)
            if os.path.isfile(os.path.join(ndir, a_fi + ".mp3")):
                f_audio = a_fi + ".mp3"
                audio = os.path.join(ndir, f_audio)
            elif os.path.isfile(os.path.join(ndir, a_fi + ".wav")):
                f_audio = a_fi + ".wav"
                audio = os.path.join(ndir, f_audio)
            md5 = hashlib.md5(open(audio, 'rb').read()).hexdigest()
        else:
            audio, f_audio, md5 = "", "", ""
        trans.setMeta('md5', md5)
        trans.setMeta('audio', f_audio)
        trans.setMeta('tgd_url', trans.name + ".TextGrid")
        trans.setMeta('morphosyntax', "oui")
        trans.setMeta('prosody', "non")
        d_comm = {'public': 'is_public', 'sous-corpus': 'subcorpus',
                  'date_enregistrement': 'recording_date',
                  'lieu_enregistrement': 'recording_location',
                  'region_enregistrement': 'recording_canton',
                  'responsable': 'owner', 'universite': 'uni',
                  'enqueteur': 'recorded_by', 'genre': 'type',
                  'transcripteur': 'transcribed_by',
                  'revised_by': 'revised_by', 'revision_date': 'revision_date'}
        d_rec = {'md5': 'checksumMD5', 'audio': 'sound_url',
                 'duree': 'duration', 'qualite': 'recording_quality'}
        d_anno = {'tgd_url': 'textgrid_url', 'morphosyntax': 'morphosyntax',
                  'prosody': 'prosody'}
        # Deal with 'reviseur'
        rev_by, rev_date = fix_reviseur()
        trans.setMeta('revised_by', rev_by)
        trans.setMeta('revision_date', rev_date)
        ida = "id=\"{0}\" name=\"{0}\"".format(trans.name)
        # Quick fix for 'duration'
        trans.setMeta('duree', "{:.04f}".format(trans.end))
        #### Write ####
        txta = txta + ("{0}<communications>\n{0}\t<communication {1}"
                       .format(taba, ida))
        txta = write_trans_arg(txta, d_comm)  # communication attributes
        txta = txta + (">\n{0}{0}<recordings>\n{0}{0}\t<recording {1}"
                       .format(taba, ida))
        txta = write_trans_arg(txta, d_rec)  # recording attributes
        txta = txta + ("/>\n{0}{0}</recordings>\n{0}{0}<annotations>\n"
                       "{0}{0}\t<annotation {1}".format(taba, ida))
        txta = write_trans_arg(txta, d_anno)  # annotation attributes
        txta = txta + ("/>\n{0}{0}</annotations>\n{0}\t</communication>\n"
                       "{0}</communications>\n".format(taba))
        return txta

    def write_spk(txta, d_spka, corpa, taba):
        """<speakers> tag."""

        # Variables
        l_elim = ['prenom', 'nom']
        d_speak = {'prenom': 'first_name', 'nom': 'last_name',
                   'sexe': 'sex', 'age': 'age_when_recorded',
                   'domicile_jeunesse': 'youth_location',
                   'domicile_attache': 'belonging_location',
                   'domicile_actuel': 'home_location',
                   'pays': 'country', 'region': 'home_canton',
                   'departement': 'home_district',
                   'habite_depuis': 'home_since_year',
                   'langage': 'french_status', 'metier': 'occupation',
                   'niveau_socioeducatif': 'socioeducational_level',
                   'annee_naissance': 'birth_year',
                   'latitude': 'latitude', 'longitude': 'longitude',
                   'extr_deb': 'extr_start', 'extr_fin': 'extr_end',
                   'geo_location_ref': 'geo_location_ref'
                   }  # 'training'?
        #### Write ####
        txta = txta + "{0}<speakers>\n".format(taba)
        for spk, d_vals in d_spka.items():
            txta = txta + ("{0}\t<speaker id=\"{1}\" name=\"{1}\""
                           .format(taba, spk))
            if '-' in d_vals.get('annee_naissance', ""):  # 'birth_date' except
                d_vals['annee_naissance'] = d_vals['annee_naissance'] \
                    .split("-", 1)[0]
            for elim in l_elim:  # pseudonymization (first/last names)
                if elim in d_vals:
                    d_vals[elim] = 'NR'
            spk_an = d_vals.get('annee_naissance')  # 'age_when_recorded'
            trs_an = trans.meta('date_enregistrement')
            if ((spk_an and not spk_an == 'NR') and
                    (trs_an and not trs_an == 'NR')):
                trs_an = trs_an.split("-", 1)[0]
                d_vals['age'] = str(int(trs_an) - int(spk_an))
            if corpa == "cfpr":  # geolocalisation
                d_vals['geo_location_ref'] = 'youth_location'
            else:
                d_vals['geo_location_ref'] = 'home_location'
            if ('extr_fin' in d_vals and not d_vals['extr_fin'] == 'NR' and
                    float(d_vals['extr_fin']) > trans.end):
                d_vals['extr_fin'] = str(trans.end)
            txta = write_spk_arg(txta, d_speak, d_vals)
            txta = txta + "/>\n"
        txta = txta + "{0}</speakers>\n".format(taba)
        return txta

    def write_part(txta, d_spka, taba):
        """<participations> tag."""

        # Variables
        d_part = {'role': 'role'}
        #### Write ####
        txta = txta + "{0}<participations>\n".format(taba)
        for spk, d_vals in d_spka.items():
            txta = txta + ("{0}\t<participation communicationID=\"{1}\" "
                           "speakerID=\"{2}\"".format(taba, trans.name, spk))
            txta = write_spk_arg(txta, d_part, d_vals)
            txta = txta + "/>\n"
        txta = txta + "{0}</participations>\n".format(taba)
        return txta

    def write_rel(txta, d_spka):
        """<relations> tag."""

        def fix_proxy(spka, d_valsa, d_rela):
            d_resa = {}
            for spk2a in d_spk:  # Filling 'd_res' with 'NR'
                if spk2a == spka:
                    continue
                if spk2a not in d_resa:
                    d_resa[spk2a] = {}
                for k in d_rela:
                    d_resa[spk2a][k] = 'NR'
            for k in d_rela:  # Replacing "NR" with values
                l_v, v = [], d_valsa.get(k)
                if not v:
                    continue
                if ";" in v:
                    l_v = v.split(";")
                elif v and (not v == 'NR'):
                    l_v = [v]
                for v in l_v:
                    s2, val = v.strip(), 'NR'
                    if "," in v:
                        s2, val = v.split(",", 1)
                        s2 = s2.strip()
                        val = val.strip()
                    if s2 in d_resa:
                        d_resa[s2][k] = val
            return d_resa
            # Variables

        taba = "\t\t\t\t"
        d_rel = {'degre_proximite': 'value', 'nature_lien': 'notes'}
        #### Write ####
        ntxt = ("\t\t<relations>\n\t\t\t<speaker_relations relationID="
                "\"proximity\">\n")
        ch = False
        for spk, d_vals in d_spka.items():
            d_res = fix_proxy(spk, d_vals, d_rel)
            if d_res:
                ch = True
            for spk2, d_vals2 in d_res.items():
                ntxt = ntxt + ("{0}<speaker_relation communicationID=\"{1}\" "
                               "speakerID_A=\"{2}\" speakerID_B=\"{3}\""
                               .format(taba, trans.name, spk, spk2))
                ntxt = write_spk_arg(ntxt, d_rel, d_vals2)
                ntxt = ntxt + "/>\n"
        if ch:
            txta = txta + ntxt + "\t\t\t</speaker_relations>\n\t\t</relations>\n"
        else:
            txta = txta + (
                "\t\t<relations>\n\t\t\t<speaker_relations relationID="
                "\"proximity\"/>\n\t\t</relations>\n")
        return txta

        # Variables

    enc = enc.replace("_", "-").upper()
    d_spk = trans.metadata.get(div, {})
    tab = "\t\t"
    corp = trans.meta("sous-corpus")
    corp = corp.split("-", 1)[0].lower() if "-" in corp else corp.lower()
    #### WRITE ####
    txt = ("<?xml version=\"1.0\" encoding=\"{0}\"?>\n"
           "<praaline_to_simple_cms version=\"2.0\">\n"
           "\t<metadata>\n".format(enc))
    txt = write_com(txt, tab)  # <communications> tag
    txt = write_spk(txt, d_spk, corp, tab)  # <speakers> tag
    txt = write_part(txt, d_spk, tab)  # <participations> tag
    txt = write_rel(txt, d_spk)  # <relations> tag
    txt = txt + "\t</metadata>\n"
    return txt


def _write_stats(trans, stats):
    """<statistics> tag."""

    def write_args(txta, d_d):
        for k, v in d_d.items():
            txta = txta + (" {}=\"{}\"".format(k, v))
        return txta

    def write_s_com(txta):
        """<communications> tag."""

        txta = txta + ("\t\t\t<communications>\n\t\t\t\t<communication "
                       "communicationID=\"{}\"".format(trans.name))
        txta = write_args(txta, stats.d_spk['trans'])
        txta = txta + "/>\n\t\t\t</communications>\n"
        return txta

    def write_s_spk(txta):
        """<speakers> tag."""

        txta = txta + "\t\t\t<speakers>\n"
        tab = "\t\t\t\t"
        for spk, d_vals in stats.d_spk.items():
            if spk == 'trans':
                continue
            d_cop = {}
            for k, v in d_vals.items():
                if not (k == "tiers" or k == "sheet"):
                    d_cop[k] = v
            txta = txta + (
                "{0}<speaker id=\"{1}\" name=\"{1}\"".format(tab, spk))
            txta = write_args(txta, d_cop)
            txta = txta + "/>\n"
        txta = txta + "\t\t\t</speakers>\n"
        return txta

    txt = "\t<statistics>\n\t\t<temporal_statistics>\n"
    stats.check_stats()
    txt = write_s_com(txt)
    txt = write_s_spk(txt)
    txt = txt + "\t\t</temporal_statistics>\n\t</statistics>\n"
    return txt


def _write_trans(stats):
    """<transcription> tag."""
    txt = ("\t<transcription text=\"{}\" word_count=\"{}\"/>\n"
           .format(stats.cont, stats.wc))
    return txt


def save_ofrom(path, trans, encoding):
    """Exports a single Transcription into an XML (OFROM) file.
    ARGUMENTS:
    - path          : (str) Full path to a directory or file.
    - trans         : (pntr) A Transcription instance.
    - encoding      : (str) The Elan file encoding.
    - l_fi          : (list) A list of files (basename with extension)
    - d_meta        : ...
    RETURNS:
    - Creates an XML file at 'path' from 'trans'.
    Note: 'path' is tested here, everything else should be known.
    Note: 'indir' should contain the TextGrid/WAV, metadata table and
          DisMo tok-tables.
    """

    # Path
    if os.path.isdir(path):  # If it's a directory
        path = os.path.join(path, trans.name + ".xml")  # Use 'trans.name'
    encoding = _ch_encoding(trans, encoding)  # Encoding
    ntrans = trans.copy()  # We use a copy from there
    l_tiers = _set_trans(ntrans)
    stats = Stats(l_tiers)
    stats.check_overlap(l_tiers)
    tseg, stats = _write_segs(l_tiers, stats)  # get SOUNDSEGMENTS/TOK_TABLE
    f = open(path, 'w', encoding=encoding)  # Open file
    f.write(_write_metadata(ntrans, encoding))  # Write <metadata>
    f.write(_write_stats(ntrans, stats))  # Write <statistics>
    f.write(_write_trans(stats))  # Write <transcription>
    f.write(tseg + "</praaline_to_simple_cms>\n")  # Write <annotation>
    f.close()


def _save_list(path, trans, encoding):
    """Exports a list of / a Corpus' transcriptions into EAF files."""
    for tr in trans:
        save_ofrom(path, tr, encoding)

    # Main function


def to_ofrom(path, trans, **args):
    """Exports one or more XMLs (OFROM).
    ARGUMENTS:
    - path          : (str) A full path to either a directory or a file.
    - trans         : (overloaded) A Transcription, Corpus or list of
                                   Transcriptions.
    - encoding      : (str) The file encoding.
    RETURNS:
    - Creates the XML(s) at 'path' from 'trans'.
    Note: Creates a copy for each Transcription while exporting.
    Note: the metadata should be already stored in 'trans'
    Note: 'trans' needs an 'omni' metadata 'audio':path-to-wav-file."""

    # Args
    encoding = args.get('encoding')  # file encoding (for all files)
    # Overload
    f = d_load.get(type(trans))
    if f:
        f(path, trans, encoding)
    else:
        raise KeyError("First argument must be of type 'Transcription/" +
                       "/Corpus/list'.")


d_load = {Transcription: save_ofrom, Corpus: _save_list,
          list: _save_list}
