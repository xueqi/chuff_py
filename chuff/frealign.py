#!/bin/env python
'''
    This is the frealign wrapper in python.
'''

from chuff.script_runner import TcshScriptRunner
from EMAN2 import EMData
import os
from shutil import copy

ACTIN_TWIST  = 167.1
ACTIN_RISE = 27.44

def run_parallel_frealign(frealign, ncpus = 4, workdir = ".", temp_dir=None, scratch_dir = None):
    '''
        parallel run frealign
    '''
    if temp_dir  is None:
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="frealign")
    if scratch_dir is None:
        scratch_dir = os.path.join(workdir, "scratch")
    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)


    # get filenames
    frealign_files = {}
    for keyname in ["F3D", "FPOI", "MAP1", "MAP2", "FWEIGH", "FINPAR",
                    "FINPAT1", "FINPAT2", "FOUTPAR", "FOUTSH"]:
        frealign_files[keyname] = frealign.get_param(keyname)
        print  keyname, frealign.get_param(keyname)
    ifirst = frealign.get_param("IFIRST")
    ilast = frealign.get_param("ILAST")
    mode = frealign.get_param("mode")
    num_per_cpu = (ilast - ifirst + 1) / ncpus + 1
    procs = []
    par_files = []
    partial_volume_files = []
    if mode == 0:
        frealign.set_parameter("FDUMP", True)
    if mode == 1:
        for i in range(ncpus):
            sdir = os.path.join(scratch_dir, "%03d" % i)
            logfile = os.path.join(sdir,"refine.log")
            if not os.path.exists(sdir):
                os.mkdir(sdir)
            first = num_per_cpu * i + ifirst
            last = num_per_cpu * (i + 1) + ifirst - 1
            if last > ilast: last = ilast
            fname = frealign.get_imagename(frealign_files["F3D"])
            fname1 = os.path.join(sdir, os.path.basename(fname))
            print "copying to %s" % fname1
            if i == 0:
                if not os.path.exists(fname1):
                    copy_volume(fname, fname1)
            else:
                if not os.path.exists(fname1):
                    copy_volume(os.path.join(os.path.join(scratch_dir, "000" ), os.path.basename(fname)), fname1)
    data = None         
    for i in range(ncpus):
        # set temporary files
        sdir = os.path.join(scratch_dir, "%03d" % i)
        logfile = os.path.join(sdir,"refine.log")
        if not os.path.exists(sdir):
            os.mkdir(sdir)
        first = num_per_cpu * i + ifirst
        last = num_per_cpu * (i + 1) + ifirst - 1
        if last > ilast: last = ilast
        for keyname, fname in frealign_files.items():
            fname1 = os.path.join(sdir, os.path.basename(fname))

            # need to split the input particles
            if keyname == "FINPAT1":
                if not os.path.exists(fname1):
                    frealign_copy_particles(fname, fname1, start = first, end = last)
            elif keyname == "FOUTPAR":
                par_files.append(fname1)
            elif keyname == "FINPAR":
                from shutil import copy
                print fname, fname1
                copy_param(fname, fname1, start = first, end=last, renumber = True)
            elif keyname == "F3D":
                partial_volume_files.append(fname1)
            frealign.set_parameter(keyname, fname1)
        # set particle numbers

        frealign.set_parameter("IFIRST", 1)
        frealign.set_parameter("ILAST", last - first + 1)

        # run frealign
        print frealign
        proc = frealign.run(return_proc = True, stdout = open(logfile,'w'), background = True)
        procs.append(proc)
    # wait for all proc
    for proc in procs:
        proc.wait()
    if mode == 0:
        frealign.set_parameter("FDUMP", False)
    for i in range(ncpus):
        # mode 0 join volume
        if mode == 1:
            join_frealign_parameter(frealign_files["FOUTPAR"], par_files)
        # mode 1 join parameter
        elif mode == 0:
            join_frealign_volume(frealign_files, partial_volume_files)

    for keyname, fname in frealign_files:
        frealign.set_parameter(keyname, fname)

    frealign.set_parameter("IFIRST", ifirst)
    frealign.set_parameter("ILAST", ilast)
def copy_param(fname, fname1, start, end = -1, renumber = True):
    print start, end
    lines = [line for line in open(fname).readlines() if not line.strip().startswith("C") and line.strip()]
    print len(lines)
    if end == -1: end = len(lines)
    if renumber:
        for i in range(start - 1, end):
            lines[i] = "%7d" % (i - start + 2) + lines[i][7:]
    open(fname1,'w').write("".join(lines[start - 1:end]))
def copy_volume(src, dst):
    if src.endswith("img") or src.endswith('hed'):
        bname = os.path.splitext(src)[0]
        d_bname =os.path.splitext(dst)[0]
        copy("%s.hed" % bname, "%s.hed" % d_bname)
        copy("%s.img" % bname, "%s.img" % d_bname)
    else:
        copy(src, dst)
def frealign_copy_particles(src, dst, start = -1, end = -1):
    if src.endswith("img") or src.endswith("hed"): # imagic file
        from EMAN2 import EMData, EMUtil
        d = EMData()
        d.read_image(src, 0, True)
        bs = d.get_xsize()
        hed = "%s.hed" % os.path.splitext(src)[0]
        img = "%s.img" % os.path.splitext(src)[0]
        d_hed = "%s.hed" % os.path.splitext(dst)[0]
        d_img = "%s.img" % os.path.splitext(dst)[0]
        if start == -1: start = 1
        h_offset = (start - 1) * 1024
        i_offset = (start - 1) * bs * bs * 4
        nptcls = EMUtil.get_image_count(src)
        if end == -1 or end > nptcls:
            end = nptcls
        nptcls = end - start + 1
        h_size = nptcls * 1024
        i_size = bs * bs * 4 * nptcls
        fhed,fimg = open(hed), open(img)
        fhed.seek(h_offset)
        fimg.seek(i_offset)
        open(d_hed,'w').write(fhed.read(h_size))
        open(d_img,'w').write(fimg.read(i_size))
        fhed.close()
        fimg.close()
        return 0
    import subprocess
    print src, dst
    args = ["e2proc2d.py", src, dst]
    if start >= 0:
        args.append('--first=%d' % start)
    if end >=0 and end >= start:
        args.append('--last=%d' % end)
    proc = subprocess.Popen(args)
    return proc.wait()

def join_frealign_parameter(outpar, input_pars, renumber = True):
    fo = open(outpar,'w')
    idx = 1
    for par_file in input_pars:
        f = open(par_file)
        lines = [line for line in f.readlines() if not line.strip().startswith("C")]
        if renumber:
            for i in range(len(lines)):
                lines[i] = "%7d" % idx + lines[7:]
                idx += 1
        fo.write("".join(lines))
        f.close()
    fo.close()

def join_frealign_volume(frealign_files, partial_volume_files):
    merge_3d_exe = "merge_3d_mp.exe"
    merge_3d_in = "%d\n" % len(partial_volume_files)
    for fname in partial_volume_files:
        merge_3d_in += "%s\n" % fname
    # write the script
    merge_3d_in += os.path.splitext(frealign_files["F3D"])[0]  + "_res\n"
    merge_3d_in += frealign_files["F3D"]  + "\n"
    merge_3d_in += frealign_files["FWEIGH"]  + "\n"
    merge_3d_in += frealign_files["MAP1"]  + "\n"
    merge_3d_in += frealign_files["MAP2"]  + "\n"
    merge_3d_in += frealign_files["FPHA"]  + "\n"
    merge_3d_in += frealign_files["FPOI"]  + "\n"
    script = ""
    script += "setenv NCPUS %d\n" % len(partial_volume_files)
    script += "%s << EOF\n" % merge_3d_exe
    script += merge_3d_in
    script += "EOF\n"
    sc = TcshScriptRunner()
    proc = sc.run_script(script, workdir = os.getcwd())
    rtn_code = proc.wait()
    return rtn_code
class FrealignParameter(object):
    def __init__(self, value = None, name = None, frealign_name = None, param_type = None, sep = ",", float_format = "%7.4f", int_format = "%d"):
        '''
            :param any value: the value of the parameter
            :param str name: the name of the parameter
            :param str feralign_name: the name used in FrealignV8
            :param type param_type: the type of the parameter, can be int, float, list,
                int is an integer,
                float is an float real
                list is a list of FrealignParameter instance,
            :param str sep: the seperator used to join the parameters in list, only used with param_type=list
            :param str float_format: the format for display float number
            :param str int_format: the format for display int number
        '''
        self.name = name
        self.frealign_name = frealign_name
        self.type = param_type
        self.sep = sep
        self.int_format = int_format
        self.float_foramt = float_format
        self.set_value(value)


    def set_value(self, value):
        try:
            self.value = self.type(value)
        except:
            print value, self.type
            raise ValueError
    def __str__(self):
        '''
            return an string respresentation of the parameter used in frealign
        '''
        if self.type == int:
            return self.int_format % self.value
        if self.type == bool:
            if self.value: return "T"
            return 'F'
        if self.type == float:
            return self.float_foramt % self.value
        if self.type == list:
            values = [str(v) for v in self.value]
            return self.sep.join(values)
        return str(self.value)

class FrealignCard(object):
    '''
        Frealign Card class, represent one line in frealign input file
    '''
    def __init__(self, cardname, newline = False):
        '''
            :param str cardname: the card name, used to retrieve the card
            :param bool newline: the str repr for the line, w/ or w/o "\n"

        '''
        self.name = cardname
        self.params = []
        self.newline = newline

    def add_param(self, after = None, *args, **kwargs):
        '''
            add parameter to the card.

            :param str after: insert after which card. None for append to the last.

        '''
        param = FrealignParameter(*args, **kwargs)
        if after is not None:
            idx = -1
            if type(after) == type(""):
                for p in self.params:
                    idx += 1
                    if p.name == after or p.frealign_name == after:
                        break
            elif type(after) == type(FrealignParameter):
                for p in self.params:
                    idx += 1
                    if p.name == after.name or p.name == after.frealign_name:
                        break

            self.params.insert(idx + 1, param)
        else:
            self.params.append(param)

    def remove_param(self, paramname):
        for param in self.params:
            if param.name == paramname or param.frealign_name == paramname:
                self.params.remove(param)
                return param
        return None

    def __str__(self):
        fp = FrealignParameter(value = self.params, param_type = list, sep = ",", name = self.name, frealign_name = self.name)
        if not self.newline:
            return str(fp)
        else:
            return str(fp) + "\n"

class FrealignScriptRunner(TcshScriptRunner):
    def __init__(self, frealign, server = None):
        TcshScriptRunner.__init__(self, server)
        self.frealign = frealign

    def get_workdir(self):
        return self.workdir


class FrealignBase(object):
    def __init__(self, version = 0):
        self.cards = [] # contains the cards
        self.executable = None
        self.version = version

    def add_card(self, card):
        self.cards.append(card)

    def get_card_index(self, cardname, from_last = False):
        its = range(len(self.cards))
        if from_last:
            its = range(len(self.cards) - 1 , -1, -1)
        for i in its:
            if self.cards[i].name == cardname:
                return i
    def get_card_at_index(self, index):
        return self.cards[index]

    def insert_card_before(self, card, before_card, from_last = False):
        before_card_index = self.get_card_index(before_card, from_last)
        after_card = self.get_card_at_index(before_card_index - 1)
        self.insert_card(card, after_card, from_last)

    def insert_card_at_index(self, card, index):
        self.cards.insert(index, card)

    def insert_card(self, card, after_card = None, from_last = False):
        '''
            insert a card into the frealign.
            :param FrealignCard card: the card to insert
            :param FrealignCard/str after_card: after which card to insert
        '''
        if after_card is None:
            self.cards.append(card)
            return
        if type(after_card) == type(FrealignCard("")):
            after_card = after_card.name
        after_card_index = self.get_card_index(after_card, from_last)
        self.cards.insert(after_card_index + 1, card)

    def add_dataset(self):
        pass

    def _get_last_card(self, cardname):
        for i in range(len(self.cards) - 1, -1, -1):
            if self.cards[i].name == cardname:
                return self.cards[i]
        return None

    def remove_card(self, cardname, from_last = False):
        idx = self.get_card_index(cardname, from_last)
        if idx >= 0:
            self.cards.remove(self.cards[idx])

    def get_card(self, cardname):
        '''
            get a card with given name
            :param str cardname: the name of the card to retrieve
            :return: FrealignCard instance, or None if not exists
        '''
        for card in self.cards:
            if card.name == cardname:
                return card
        return None

    def basic_config(self):
        pass
    def initCards(self):
        pass

    def get_param(self, paramname):
        for card in self.cards:
            for param in card.params:
                if paramname == param.name or paramname == param.frealign_name:
                    return param.value
        return None
    def set_parameter(self, paramname, paramvalue):
        for card in self.cards:
            for param in card.params:
                if param.name.startswith(paramname)  or param.frealign_name.startswith(paramname):
                    param.set_value(paramvalue)
                    return
        exc_str = "Can not find parameter with name: %s\n" % paramname
        exc_str += "Available parameters are:\n"
        for card in self.cards:
            exc_str += ", ".join([param.name for param in card.params])
            exc_str += "\n"
        raise Exception, exc_str

    def get_image_basename(self, fname):
        '''
            get image name without extension
        '''
        bname, ext = os.path.splitext(fname)
        cform = self.get_param("CFORM")
        if cform == "I" and (ext ==".img" or ext == ".hed"):
            return bname
        if cform == "S":
            return bname
        if cform == "M":
            return bname
        return fname
    def turn_on(self, *args):
        '''
            options are:
        '''
        for paramname in args:
            for card in self.cards:
                for p in card.params:
                    if p.name == paramname or p.frealign_name == paramname:
                        if p.type == bool:
                            p.set_value(True)

    def turn_off(self, *args):
        for paramname in args:
            for card in self.cards:
                for p in card.params:
                    if p.name == paramname or p.frealign_name == paramname:
                        if p.type == bool:
                            p.set_value(False)

    def __str__(self):
        ss = []
        for card in self.cards:
            ss.append(str(card))
        return "\n".join(ss)

    def run(self, project = None, server = None, stdout = None, background = False, workdir = ".", return_proc = True):
        sr = FrealignScriptRunner(self)
        import tempfile
        script_file = tempfile.NamedTemporaryFile(prefix="frealign_script", delete=False)
        sr.script = script_file.name
        self.write_frealign_input_file(script_file, workdir = workdir)
        script_file.close()
        if background:
            return sr.run(stdout = stdout, background = True, return_proc = return_proc)
        else:
            return sr.run(stdout = stdout)

    def write_frealign_input_file(self, script_file, workdir = "."):
        if type(script_file) == type(""):
            sc = open(script_file,'w')
        else:
            sc = script_file
        sc.write("#!/bin/tcsh\n\n")
        sc.write("cd %s\n" % os.path.join(os.getcwd(), workdir))
        sc.write("%s << EOF\n" % self.executable)
        sc.write(self.__str__())
        sc.write("\nEOF\n")
        sc.close()

    def cleanup(self):
        pass



class Frealign8(FrealignBase):
    def __init__(self, version = 8.):
        FrealignBase.__init__(self, version)
        self.executable = "frealign_v8_mp_cclin"
        self.scratch_dir = None
    def set_scratch_dir(self, d):
        self.scratch_dir = d
    def initCards(self):
        card = FrealignCard("card1")
        card.add_param(value = "I", name = "file_format", frealign_name = "CFORM", param_type = str)
        card.add_param(None, 0, "mode", "IFLAG", int)
        card.add_param(None, False, "refine_magnification", "FMAG", bool)
        card.add_param(None, False, "refine_defocus", "FDEF", bool)
        card.add_param(None, False, "refine_astigmitism", "FASTIG", bool)
        card.add_param(None, False, "refine_individual_defocus", "FPARAT", bool)
        card.add_param(None, 0, "ewald_correction", "IEWALD", int)
        card.add_param(None, False, "apply_symmetry", "FBEAUT", bool)
        card.add_param(None, False, "apply_fom_filter", "FCREF", bool)
        card.add_param(None, False, "output_prj_match", "FMATCH", bool)
        card.add_param(None, 0, "calc_fsc", "IFSC", int)
        card.add_param(None, False, "calc_statistics", "FSTAT", bool)
        card.add_param(None, 1, "padding_factor", "IBLOW", int)
        self.add_card(card)

        card = FrealignCard('card2')
        card.add_param(None, 0, "outer_radius", "RO", float, float_format="%.4f")
        card.add_param(None, 0, "inner_radius", "RI", float)
        card.add_param(None, 0, "pixel_size", "PSIZE", float)
        card.add_param(None, 0, "weight", "WGH", float)
        card.add_param(None, 0, "mask_std", "XSTD", float)
        card.add_param(None, 0, "phase_residual_constant", "PBC", float)
        card.add_param(None, 0, "average_phase_residue", "BOFF", float)
        card.add_param(None, 0, "angular_step_size", "DANG", float)
        card.add_param(None, 0, "max_cycle_search", "ITMAX", int)
        card.add_param(None, 0, "max_match_test", "IPMAX", int)
        self.add_card(card)

        card = FrealignCard('card3')
        card.add_param(None, '1 1 1 1 1', "parameter_mask", "PMASK", str)
        self.add_card(card)

        card = FrealignCard('card4')
        card.add_param(None, 1, 'first_particle', 'IFIRST', int)
        card.add_param(None, 1, 'last_particle', 'ILAST', int)
        self.add_card(card)
        card = FrealignCard("card5")
        card.add_param(None, "C1", "symmetry", "ASYM", str)
        self.add_card(card)

        card = self._create_data_end_card()
        self.add_card(card)

        self.add_card(self.create_file_name_card("card13", "f3d", "output_volume", "F3D"))
        self.add_card(self.create_file_name_card("card14", "fweight", "weight_volume", "FWEIGH"))
        self.add_card(self.create_file_name_card("card15", "fsc1", "first_half", "MAP1"))
        self.add_card(self.create_file_name_card("card16", "fsc2", "second_haf", "MAP2"))
        self.add_card(self.create_file_name_card("card17", "fpha", "phase_residue_volume", "FPHA"))
        self.add_card(self.create_file_name_card("card18", "fpoi", "point_spread_volume", "FPOI"))


    def basic_config(self):
        self.set_parameter("XSTD", 0)


    def _create_card10b(self, cardname, mg, more = 1):
        card = FrealignCard(cardname)
        nin, absmagpin, ifilmin, dfmid1in, dfmid2in, angastin = mg
        card.add_param(None, nin, "number_of_particles", "NIN", int)
        card.add_param(None, absmagpin, "magnification", "ABSMAGPIN", float)
        card.add_param(None, ifilmin, "film_number", "IFILMIN", int)
        card.add_param(None, dfmid1in, "defocus1", "DFMID1IN", int)
        card.add_param(None, dfmid2in, "number_of_particles", "DFMID2IN", int)
        card.add_param(None, angastin, "number_of_particles", "ANGASTIN", int)
        card.add_param(None, more, "number_of_particles", "MORE", int)
        return card

    def add_dataset(self, magnification, dstep, target, thresh, cs, akv, tx, ty,
                    rrec, rmax1, rmax2, dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh,
                    mgs = None, rclas = 10):
        cards = []
        cards.append(self._create_card6(magnification, dstep, target, thresh, cs, akv, tx, ty))
        card = FrealignCard('card7')
        card.add_param(None, rrec, "reconstruct_resolution", "RREC", float, float_format="%.4f")
        card.add_param(None, rmax1, "refinement_resolution_max", "RMAX1", float)
        card.add_param(None, rmax2, "refinement_resolution_min", "RMAX2", float)
        if self.version > 9.065: # from 9.07
            card.add_param("RMAX2", rclas, "resolution_limit_classification", "RCLAS", float)
        card.add_param(None, dfstd, "defocus_uncertainty", "DFSTD", float)
        card.add_param(None, rbfact, "refinement_bfactor", "RBFACT", float)
        cards.append(card)

        cards.append(self.create_file_name_card("card8", finpat1, "particle_stack", "FINPAT1"))
        cards.append(self.create_file_name_card("card9", finpat2, "reprojection_matching", "FINPAT2"))
        if finpar is not None:
            cards.append(self.create_file_name_card("card10", finpar, "input_param", "FINPAR"))
        else:
            if mgs is not None:
                for mg in mgs:
                    card = self._create_card10b("card10", mg)
                    cards.append(card)
                cards.append(self._create_card10b("card10", [0,0,0,0,0,0], 0))
        cards.append(self.create_file_name_card("card11", foutpar, "output_params", "FOUTPAR"))
        cards.append(self.create_file_name_card("card12", foutsh, "output_shifts", "FOUTSH"))

        idx = self.get_card_index("card6", from_last = True)
        for card in cards:
            self.insert_card_at_index(card, idx)
            idx += 1


    def _create_card5b(self, alpha, rise, nsubunits = 1, nstarts = 1, stiffness = 0.00001):
        card = FrealignCard("card5b")
        card.add_param(None, alpha, "helical_turn", "ALPHA", float)
        card.add_param(None, rise, "helical_rise", "RISE", float)
        card.add_param(None, nsubunits, "number_subunits", "NSUBUNITS", int)
        card.add_param(None, nstarts, "number_starts", "NSTARTS", int)
        card.add_param(None, stiffness, "stiffness", "STIFFNESS", float, float_format = "%.5f")
        return card

    def _create_card6(self, realmag, dstep, target, thresh, cs, akv, tx, ty):
        card = FrealignCard('card6')
        card.add_param(None, realmag, "magnification", "RELMAG", float, float_format = "%.4f")
        card.add_param(None, dstep, "detector_step", "DSTEP", float, float_format = "%.4f")
        card.add_param(None, target, "target_phase_residue_refine", "TARGET", float, float_format = "%.4f")
        card.add_param(None, thresh, "phase_residue_threshold", "THRESH", float, float_format = "%.4f")
        card.add_param(None, cs, "spherial_aberration", "CS", float, float_format = "%.4f")
        card.add_param(None, akv, "voltage_kv", "AKV", float, float_format="%.4f")
        card.add_param(None, tx, "beam_tilt_x", "TX", float)
        card.add_param(None, ty, "beam_tilt_y", "TY", float)
        return card

    def _create_data_end_card(self):
        card6 = self._create_card6(0,0,0,0,0,0,0,0)
        return card6
    def create_file_name_card(self, cardname, filename, paramname, frealign_name):
        card = FrealignCard(cardname)
        card.add_param(None, filename, paramname, frealign_name, str)
        return card

    def set_symmetry(self, asym, *args, **kwargs):
        self.set_parameter("ASYM", asym)
        self.remove_card("card5a")
        self.remove_card("card5b")
        if asym == "H":
            card5b = self._create_card5b(*args, **kwargs)
            idx = self.get_card_index("card5")
            self.insert_card_at_index(card5b, idx + 1)

    def set_pixel_size(self, pixel_size):
        self.set_parameter("PSIZE")

    def set_output_volume(self, output_volume):
        self.set_parameter("f3d", output_volume)

class Frealign9(Frealign8):
    def __init__(self, version = 9.09):
        Frealign8.__init__(self, version)
        self.executable = "frealign_v9.exe"
        self.workdir = "."
    def initCards(self):

        Frealign8.initCards(self)
        # card1
        card1 = self.get_card('card1')
        card1.remove_param("FCREF")
        card1.add_param("FBEAUT", False, "filter", "FFILT", bool )
        card1.add_param("FFILT", False, "bfactor", "FBFACT", bool)
        card1.remove_param("FSTAT")
        card1.remove_param("IBLOW")
        card1.add_param(None, False, "dump_partial_volume", "FDUMP", bool)
        card1.add_param(None, 0, "memory_usage", "IMEM", int)
        card1.add_param(None, 0, "interpolation_scheme", "INTERP", int)

        # card2
        card2 = self.get_card('card2')
        card2.add_param("PSIZE", 0, "molecule_weight", "MW", float)

    def get_param_full_path(self, par, directory = None):
        if directory is None:
            directory = os.getcwd()
        return os.path.join(directory, par.split("/")[-1])
    def get_imagename(self, vol, directory = None, ext = None):
        '''
            get file name, represent the true image file in the file system. eg. with extension
        '''
        if directory is None:
            directory = os.getcwd()
        cform = self.get_param("CFORM")
        bname, ext1 = os.path.splitext(vol)
        ext1 = ext1[1:]
        if cform == "I":
            # imagic
            ext = "img"
            if ext1 == "img" or ext1 == "hed":
                pass
            else:
                bname = vol
        elif cform == "S":
            ext = "spi"
        elif cform == "M":
            ext = 'mrc'
        else:
            ext = None
        if ext is not None:
            return ".".join([bname, ext])
        else:
            return vol

    def turn_on(self, *args):
        super(Frealign9, self).turn_on(*args)
        if "cryo" in args:
            self.set_parameter("WGH", 0.07)

    def run_parallel_local(self, ncpus = 4):
        if self.scratch_dir is None:
            import tempfile
            scratch_dir = os.path.join(self.workdir, '.scratch')
            if not os.path.exists(scratch_dir):
                os.mkdir(scratch_dir)
            self.scratch_dir = tempfile.mkdtemp(prefix = "frealign", dir = os.path.join(self.workdir, ".scratch"))

        if not os.path.exists(self.scratch_dir):
            os.makedirs(self.scratch_dir)
        log_dir = os.path.join(self.workdir, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        # mode 0 for reconstruction only
        mode = self.get_param("mode")
        if mode == 0 or mode == 1:
            if mode == 0:
                self.turn_on("FDUMP")
                self.turn_off("calc_fsc")

            ptcl_num = self.get_param("ILAST")

            nptcl_per_cpu = ptcl_num / ncpus + 1
            procs = []
            if mode == 0:
                merge_3d_in = "%s\n" % ncpus
            out_vol = self.get_param("F3D")
            out_par = self.get_param("FOUTPAR")
            if mode == 1:
                vol_name = self.get_imagename(out_vol)
                vol = EMData()
                vol.read_image(vol_name, 0, False, None, True)
            for i in range(ncpus):
                log_file = os.path.join(log_dir, "%s_%d.log" % (os.path.splitext(os.path.basename(out_vol))[0], i))
                ifirst = nptcl_per_cpu * i + 1
                ilast = nptcl_per_cpu * (i + 1)
                if ilast > ptcl_num:
                    ilast = ptcl_num

                self.set_parameter("IFIRST", ifirst)
                self.set_parameter("ILAST", ilast)
                self.set_parameter("F3D", "%s_%d" % (out_vol, i))

                # for each copy of process, we make a copy of all files needed.
                # The Input particles for each process,
                # the input volume for each process,
                # the input parameters for each process,
                # the output parameter for each process



                if mode == 0:

                    merge_3d_in +="%s_%d.hed\n" % (out_vol, i)
                elif mode == 1: # split the output par

                    self.set_parameter("FOUTPAR", "%s_%d" % (out_par, i))
                    vol.write_image(self.get_imagename("%s_%d" % (out_vol, i)))
                proc = self.run(background = True, return_proc = True, stdout = open(log_file, 'w'))
                procs.append(proc)
            del vol
            # wait all process done
            for proc in procs:
                rtn_code = proc.wait()
                if rtn_code != 0:
                    print "proc %d exits with error: %d\n" % (proc.pid, rtn_code)
                    return
            # restore parameters

            self.set_parameter("ILAST", ptcl_num)
            self.set_parameter("IFIRST", 1)

            # merge the volume
            if mode == 0:
                merge_3d_exe = "merge_3d_mp.exe"

                # write the script
                self.set_parameter("F3D", out_vol)
                self.turn_off("FDUMP")
                merge_3d_in += self.get_param("F3D") + ".res\n"
                merge_3d_in += self.get_param("F3D") + "\n"
                merge_3d_in += self.get_param("FWEIGH") + "\n"
                merge_3d_in += self.get_param("MAP1") + "\n"
                merge_3d_in += self.get_param("MAP2") + "\n"
                merge_3d_in += self.get_param("FPHA") + "\n"
                merge_3d_in += self.get_param("FPOI") + "\n"
                script = ""
                script += "setenv NCPUS %d\n" % ncpus
                script += "%s << EOF\n" % merge_3d_exe
                script += merge_3d_in
                script += "EOF\n"
                sc = TcshScriptRunner()
                print script
                proc = sc.run_script(script, workdir = os.getcwd())
                rtn_code = proc.wait()

                if rtn_code != 0:
                    print "ERror with merge_3d: rtn=%d\n" % rtn_code

                else:
                    # clean up
                    for i in range(ncpus):
                        os.remove("%s_%d.hed" % (out_vol, i))
                        os.remove("%s_%d.img" % (out_vol, i))
            elif mode == 1:
                # merge parameters to out_par
                opar = open(out_par,'w')
                for i in range(ncpus):
                    # clean up the volume
                    os.remove("%s_%d.hed" % (out_vol, i))
                    os.remove("%s_%d.img" % (out_vol, i))
                    # combine the parameter
                    ipar = "%s_%d" % (out_par, i)
                    f = open(ipar)
                    line = f.readline()
                    if i == 0:
                        # write header
                        while True:
                            if len(line) == 0: break
                            if not line.strip().startswith("C"): break
                            opar.write(line)
                            line = f.readline()
                        # write data
                        while True:
                            if len(line) == 0: break
                            if line.strip().startswith("C"): continue
                            opar.write(line)
                            line = f.readline()
                    else:
                        # write data only
                        while True:
                            if len(line) == 0: break
                            if line.strip().startswith("C"): continue
                            opar.write(line)
                            line = f.readline()
                    f.close()
                    # remove the intermidate files
                    os.remove(ipar)
                opar.close()

class FrealignHelical(object):
    def __init__(self, twist = 0, rise = 0, version = 9):
        self.version = version
        if version == 9:
            self.frealign = Frealign9()
        else:
            self.frealign = Frealign8()
        self.frealign.initCards()
        self.twist = twist
        self.rise = rise
        self.frealign.set_symmetry("H", twist, rise)
    def set_parameter(self, paramname, paramvalue):
        if paramname in ["F3D"]:
            paramvalue = self.frealign.get_image_basename(paramvalue)
        self.frealign.set_parameter(paramname, paramvalue)

    def __str__(self):
        return str(self.frealign)

class FrealignActin(FrealignHelical):
    def __init__(self, output_dir = None, tag = "", version = 9):
        FrealignHelical.__init__(self, ACTIN_TWIST, ACTIN_RISE, version)
        self.frealign.turn_on("calc_fsc", "cryo")
        self.output_dir = output_dir
        self.tag = tag
        if self.output_dir is None:
            self.output_dir = os.getcwd()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.saves = ["F3D", "MAP1", "MAP2"]
        self.temp_dir = os.path.join(self.output_dir, "temp")
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)
        self.setup_files()
    def setup_files(self):
        for paramname, paramvalue in [
            ("F3D", "vol"), ("FWEIGH", "weight"),
            ("MAP1", "fsc1"), ("MAP2", "fsc2"),
            ("FPHA", "fpha"), ("FPOI", "poi")
                                      ]:
            if paramname in self.saves:
                self.set_parameter(paramname, os.path.join(self.output_dir, "%s_%s" % (paramvalue, self.tag)))
            else:
                self.set_parameter(paramname, os.path.join(self.temp_dir, "%s_%s" % (paramvalue, self.tag)))

class FrealignActoMyosinVirginia(FrealignActin):
    def __init__(self, output_dir = "frealign_bin1_gold3", tag="test"):
        FrealignActin.__init__(self, output_dir, tag)
        self.set_parameter("voltage", 300)
        self.set_parameter("outer_radius", 200)
        self.set_parameter('detector_step', 14)
        self.set_parameter("spherial_aberration", 2.7)
        self.set_parameter("pixel_size", 1.08714)
        self.set_parameter("molecule_weight", 150)
        self.set_parameter("phase_residual_constant", 1000)
        self.set_parameter("angular_step", 30)
        self.set_parameter("max_cycle_search", 50)
        self.set_parameter("max_match_test", 10)
    def set_scratch_dir(self, d):
        self.frealign.set_scratch_dir(d)
    def add_dataset(self, file_stack, param_file, output_param_file):
        dstep = 14
        target = 90
        thresh = 90
        cs = 2.7
        akv = 300
        tx = 0
        ty = 0
        rrec = self.frealign.get_param("pixel_size") * 2
        rmax1 = 200
        rmax2 = 10
        dfstd = 1000
        rbfact = 0
        finpat1 = file_stack
        finpat2 = os.path.join(self.output_dir,"finpat2")
        finpar = param_file
        foutpar = os.path.join(self.output_dir, output_param_file)
        foutsh = os.path.join(self.output_dir, "foutsh")
        self.frealign.add_dataset(1, dstep, target, thresh, cs, akv, tx, ty, rrec, rmax1, rmax2,
                                   dfstd, rbfact, finpat1, finpat2, finpar, foutpar, foutsh)
        nptcls = len([line for line in open(param_file).read().strip().split("\n") if not line.strip().startswith("C")])
        self.set_parameter("last_particle", nptcls)

    def run(self):
        self.frealign.run()

###############################################################################

def resize_stack(input_stack, output_stack, new_size):
    '''
        resize the stack to new_size. This is mainly clip the particle in the center. Used only for frealign.
        Does not support mrc.

        :param str input_stack: the input stack file name
        :param str output_stack: the output stack file name
        :param int new_size: the new size of the particles
    '''
    from EMAN2 import EMData, Region
    ptcls = EMData.read_images(input_stack)
    old_size = ptcls[0].get_xsize()
    print old_size
    l = (old_size - new_size) / 2

    nptcls = len(ptcls)
    if nptcls == 1: # this is a 3D stack
        r = Region(l, l, 0, new_size, new_size, nptcls)
    else:
        r = Region(l, l, new_size, new_size)
    for ptcl in ptcls:
        ptcl.clip_inplace(r)
    for i in range(len(ptcls)):
        ptcl.write_image(output_stack, i)

if __name__ == "__main__":
    # frealign reconstruct need :
    #    an input parameter file
    #    an input particle stacks
    #    an output directory
    import argparse

    parser = argparse.ArgumentParser(description="FrealignV8 commandline wrapper.\nUse: frealign.py --params=frealign_bin1_gold1/chuck_apomyoIb_201501_5.par --output_dir=frealign_bin1_gold1 --apix=4.35 --ptcls=frealign_bin1_gold1/frealign_image_stack.hed --dp=28.14 --dphi=167.1")

    parser.add_argument("--apix", type = float, default = 1.,
                        help = "Pixel size of the particles and the volume")
    parser.add_argument("--dp", type = float, default = 1.,
                        help = "helical rise of the filament")
    parser.add_argument("--cores", type = int, default = 16,
                        help = "number of cores")
    parser.add_argument("--dphi", type = float, default = 1.,
                        help = "helical rise of the filament")
    parser.add_argument("--rmax", type = float, default = -1,
                        help = "helical rise of the filament")
    parser.add_argument("--params", default = None,
                        help = "frealign input parameters")
    parser.add_argument("--ptcls", help = "frealign input particles stack")
    parser.add_argument("--output_dir", default = ".",
                         help = "frealign output directory")
    parser.add_argument("--frealign_exec", default = None,
                         help = "frealign executable, can be used to switch to mp version")

    parser.add_argument("--task", default = "reconstruct", help = "tasks: reconstruct, alignment, resize")

    # resize stack options

    parser.add_argument("--new_size", default = None, type=int, help = "new size of the stack")
    parser.add_argument("--output_stack", default = None, help = "output for the resized particles")

    options, other_options = parser.parse_known_args()

    if options.task == "resize":
        if options.new_size is None or options.output_stack is None:
            raise Exception, "must provide new_size and output_stack option fo resizing"
        resize_stack(options.ptcls, options.output_stack, options.new_size, isvolume = options.volume)
        exit()
    elif options.task == "reconstruct":
        #if not os.path.exists(input_params):
        #    raise Exception, "Can not find input paramaters: %s" % input_params

        # get the number of total particles
        from EMAN2 import EMUtil, EMData
        n_ptcls = EMUtil.get_image_count(options.ptcls)

        if n_ptcls <= 1:
            data = EMData()
            data.read_image(options.ptcls, 0, header_only=True)
            n_ptcls = data.get_zsize()
            del data
            data = EMData()
            data.read_image(options.ptcls, 0, True)
            xsize = data.get_xsize()
        else:
            data = EMData()
            data.read_image(options.ptcls, 0, True)
            xsize = data.get_xsize()
        if options.rmax <= 0:
            ro = xsize / 2 - 1
        else:
            ro = options.rmax

        input_params = options.params
        output_root = os.path.join(options.output_dir, os.path.splitext(os.path.basename(input_params))[0])

        d = {
#            "FINPAR" : os.path.join(os.getcwd(), input_params),
            "ILAST"  : n_ptcls,
            "RO" : ro,
            "RISE" : options.dp,
            "ALPHA" : -options.dphi,

            }
        print d

        #fr.set(d)
    elif options.task == "refine":
        pass
