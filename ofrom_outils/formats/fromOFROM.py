from corflow.Transcription import Transcription
import xml.etree.cElementTree as ETree
import os,re,html

def _checkFiles(path,ch_ext=".xml"):
    """Returns a list of '.xml' files."""
    def _checkFile(fpath,file,l_files):
        fi,ext = os.path.splitext(file); 
        if not ext.lower() == ch_ext:
            return
        l_files.append((fpath,fi)) 
    
    l_files = []; ch_dir = 0
    if os.path.isdir(path):        # 'path' is a directory
        for file in os.listdir(path):
            p = os.path.join(path,file)
            _checkFile(p,file,l_files)
        ch_dir = 1
    elif os.path.isfile(path):     # 'path' is a file
        file = os.path.basename(path)
        _checkFile(path,file,l_files)
    else:
        return [],-1
    return l_files,ch_dir

def _readMeta(trans,elem):
    """<metadata> tag, fills 'trans' metadata."""
    
    l_subs = ['communication','recording','annotation'] # communications
    for n in l_subs:
        sub = None
        for el in elem.iter():
            if el.tag == n:
                sub = el; break
        for k,v in sub.attrib.items():
            trans.setMeta(k,v)
    l_subs = elem.findall('speaker')                    # speakers
    for sub in l_subs:
        spk = sub.get('name'); d_vals = {}
        for k,v in sub.attrib.items():
            d_vals[k] = v
        trans.addSpk(spk,d_vals)
    l_subs = elem.findall('participation')              # participations
    d_spk = trans.metadata.get('speakers',{})
    for sub in l_subs:
        spk = sub.get('speakerID'); role = sub.get('role')
        trans.setSpk(spk,"role",role)
    l_subs = elem.findall('speaker_relation')           # relations
    for sub in l_subs:
        spk = sub.get('speakerID_A'); spk2 = sub.get('speakerID_B')
        prox,nat = sub.get('value'),sub.get('notes')
        val = d_spk[spk].get('value',"")+";"+spk2+","+prox
        trans.setSpk(spk,"value",val)
        val = d_spk[spk].get('notes',"")+";"+spk2+","+nat
        trans.setSpk(spk,"value",val)
        # Fix 'value' and 'notes'
    for spk,d_vals in d_spk.items():
        l_fix = [("value",d_vals.get('value')),("notes",d_vals.get('notes'))]
        for k,val in l_fix:
            if val:
                val = val.strip(";")
                trans.setSpk(spk,k,val)
def _readStats(trans,elem):
    """<statistics> tag, fills 'trans' metadata."""
    selem = elem.find("temporal_statistics")
    com, l_spk = None, []
    for sub in selem.iter():
        if sub.tag == "communication":
            com = sub
        elif sub.tag == "speaker":
            l_spk.append(sub)
    for k, v in com.attrib.items():
        trans.setMeta(k, v, "stats")
    for sub in l_spk:
        div = "stats_"+sub.get('name', "")
        for k, v in sub.attrib.items():
            trans.setMeta(k, v, div)
    selem, k = elem.find("transcription"), "word_count"
    trans.setMeta(k, selem.attrib[k], "stats")
def _readTrans(trans,elem):
    """<table_soundsegment> tag, fills main tiers."""
    for sub in elem.iter('soundsegment'):
        spk,text = sub.get('speaker_id'),html.unescape(sub.get('text'))
        tmin,tmax = float(sub.get('tmin','-1.')),float(sub.get('tmax','-1.'))
        ntier = trans.getName(spk)
        if spk and not ntier:
            ntier = trans.create(-1,spk)
        ntier.create(-1,"",tmin,tmax,text)
def _readAnno(trans,elem):
    """<table_tok_min/mwu>, fills annotation tiers."""

    def dealWithLemma(sub,spk,tmin,tmax):
        #l_ncont = [sub.get('lemma',""),
        #           sub.get('pos_ext_min',""),
        #           sub.get('pos_ext_mwu',""),
        #           sub.get('disfluency',""),
        #           sub.get('discourse',"")]
        nname = spk+"[lemma]"; ntier = trans.getName(nname)
        if spk and not ntier:
            ptier = trans.getName(spk)
            i = ptier.index()+1 if ptier else -1
            ntier = trans.create(i,nname)
        nseg = ntier.getTime(tmin)
        if not nseg:
            nseg = ntier.create(-1,"",tmin,tmax,sub.get('lemma', ""))
            # l_cont = l_ncont
        else:
            nseg.content = sub.get('lemma', "")
            #l_cont = nseg.content.split("|"); lc = len(l_cont)
            #for a in range(len(l_ncont)):
            #    if a >= lc:
            #        break
            #    elif l_ncont[a] and not l_cont[a]:
            #        l_cont[a] = l_ncont[a]
        #nseg.content = ""
        #for cont in l_cont:
        #    nseg.content = nseg.content+"|"+cont
        #nseg.content = html.unescape(nseg.content)
        #if nseg.content.startswith("|"):
        #    nseg.content = nseg.content[1:]
    def dealWithAnno(sub, minwu, spk, tmin, tmax, typ):
        pmin,pmwu = sub.get('pos_min'),sub.get('pos_mwu')
        if typ == "pos":
            txt = pmin if pmin else pmwu
        else:
            txt = sub.get('text')
        nname = spk+"["+typ+"_"+minwu+"]"; ntier = trans.getName(nname)
        if spk and not ntier:
            ptier = trans.getName(spk)
            i = ptier.index()+1 if ptier else -1
            ntier = trans.create(i,nname)
        ntier.create(-1,"",tmin,tmax,html.unescape(txt))
    
    minwu = "min" if elem.tag.endswith("_min") else "mwu"
    debug = True
    for sub in elem.iter('tok'+minwu):
        spk = sub.get('speaker_id')
        tmin,tmax = float(sub.get('tmin','-1.')),float(sub.get('tmax','-1.'))
        if 'lemma' in sub.keys():
            dealWithLemma(sub,spk,tmin,tmax)            # lemma tier
        dealWithAnno(sub,minwu,spk,tmin,tmax,"pos")     # PoS tier
        dealWithAnno(sub,minwu,spk,tmin,tmax,"tok")     # Tok tier
d_OFROMoper = {'metadata':_readMeta,
               'statistics':_readStats,
               'table_soundsegment':_readTrans,
               'table_tok_mwu':_readAnno,
               'table_tok_min':_readAnno}
def loadOFROM(path,name=""):
    """Main function to load a given (OFROM) XML file.
    ARGUMENTS:
    - path          : (str) A full path to the file.
    - name          : (str) The Transcription name.
    RETURNS:
    - trans         : (pntr) A Transcription instance.
    Note: assumes encoding (and 'name') is known."""
    
        # Variables
    trans = Transcription(name=name,metadata={})
    root,b_root = None,False; par = None
        # Read the file (with Etree)
    for event, elem in ETree.iterparse(path, events=("start","end")):
            # Find root for operation (cleaning)
        if not b_root:
            root = elem; b_root = True
        elif event == "end":
            f = d_OFROMoper.get(elem.tag)
            if f:
                f(trans,elem)
                try:
                    root.remove(elem)
                except:
                    par = root.find('annotation')
                    par.remove(elem)
    trans.renameSegs(); trans.setBounds()
    return trans
    # Main function
def fromOFROM(path,**args):
    """Imports one or more XML(s) (OFROM).
    ARGUMENTS:
    - path          : (str) A full path to either a file or a directory.
    RETURNS:
    - trans/l_trans : (pntr/list) Either a Transcription or a list of
                                  Transcriptions."""
    
        # Get files
    l_files,ch_dir = _checkFiles(path)
    if ch_dir == 1:                 # list of files
        l_trans = []
        for tup in l_files:
            l_trans.append(loadOFROM(*tup))
        return l_trans
    elif ch_dir == 0 and l_files:   # single file
        return loadOFROM(*l_files[0])