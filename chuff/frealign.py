#!/bin/env python
'''
    This is the frealign wrapper in python.
'''

from collections import OrderedDict
from chuff.script_runner import TcshScriptRunner

from chuff.includes.server_configs.program_settings import FREALIGN_EXEC, FREALIGN_MP_EXEC

import os

ACTIN_TWIST  = 167.1
ACTIN_RISE = 27.44

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
    def __init__(self, cardname, newline = False):
        self.name = cardname
        self.params = []
        self.newline = newline
    def add_param(self, after = None, *args, **kwargs):
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
        self.add_card(self.create_file_name_card("card14", "fweight", "weight_volume", "FWEIGHT"))
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
                    mgs = None, rclas=0):
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
        self.scratch_dir = None
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
            os.mkdir(self.scratch_dir)
        log_dir = os.path.join(self.workdir, "logs")
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        # mode 0 for reconstruction only
        if self.get_param("mode") == 0:
            self.turn_on("FDUMP")
            self.turn_off("calc_fsc")
            import subprocess
            ptcl_num = self.get_param("ILAST")

            nptcl_per_cpu = ptcl_num / ncpus + 1
            procs = []
            merge_3d_in = "%s\n" % ncpus
            out_vol = self.get_param("F3D")
            for i in range(ncpus):
                log_file = os.path.join(log_dir, "%s_%d.log" % (os.path.splitext(os.path.basename(out_vol))[0], i))
                ifirst = nptcl_per_cpu * i + 1
                ilast = nptcl_per_cpu * (i + 1)
                if ilast > ptcl_num:
                    ilast = ptcl_num

                self.set_parameter("IFIRST", ifirst)
                self.set_parameter("ILAST", ilast)
                self.set_parameter("F3D", "%s_%d" % (out_vol, i))
                merge_3d_in +="%s_%d.hed\n" % (out_vol, i)
                proc = self.run(background = True, return_proc = True, stdout = open(log_file, 'w'))
                procs.append(proc)
            # wait all process done
            for proc in procs:
                rtn_code = proc.wait()
                if rtn_code != 0:
                    print "proc exits with error: %d\n" % rtn_code
                    #return
            # restore parameters

            self.set_parameter("ILAST", ptcl_num)
            self.set_parameter("IFIRST", 1)
            self.set_parameter("F3D", out_vol)

            # merge the volume

            merge_3d_exe = "merge_3d_mp.exe"

            # write the script
            self.set_parameter("F3D", out_vol)
            merge_3d_in += self.get_param("F3D") + ".res\n"
            merge_3d_in += self.get_param("F3D") + "\n"
            merge_3d_in += self.get_param("FWEIGHT") + "\n"
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
            ("F3D", "vol"), ("FWEIGHT", "weight"),
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
        self.set_parameter("outer_radius", 250)
        self.set_parameter('detector_step', 14)
        self.set_parameter("spherial_aberration", 2.7)
        self.set_parameter("pixel_size", 1.08714)
        self.set_parameter("molecule_weight", 150)
        self.set_parameter("phase_residual_constant", 1000)
        self.set_parameter("angular_step", 30)
        self.set_parameter("max_cycle_search", 50)
        self.set_parameter("max_match_test", 10)

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
class FrealignV8(object):

    '''
        Each FREALIGN_EXEC instance must set the following:
        RO, PSIZE, CFORM, ILAST,
        ALPHA, RISE,
        RELMAG, DSTEP,
        RREC,
        FINPART1,
    '''

    def __init__(self, params = {}, version = 9):
        self.params = OrderedDict()
        self.exec_version = version
        self.mp = True

        #if self.exec_version == 8:
        self.card1 = "CFORM,IFLAG,FMAG,FDEF,FASTIG,FPART,IEWALD,FBEAUT,FCREF,FMATCH,IFSC,FSTAT,IBLOW".split(",")
        self.card2 = "RO,RI,PSIZE,WGH,XSTD,PBC,BOFF,DANG,ITMAX,IPMAX".split(",")
        self.card3 = ["PMASK"]
        #elif self.exec_version == 9:
        #    self.card1 = "CFORM,IFLAG,FMAG,FDEF,FASTIG,FPART,IEWALD,FBEAUT,FFILT,FBFACT,FMATCH,IFSC,FDUMP,IMEM,INTERP".split(",")
        #    self.card3 = ["PMASK", "DMASK"]
        #    self.card2 = "RO,RI,PSIZE,MW,WGH,XSTD,PBC,BOFF,DANG,ITMAX,IPMAX".split(",")
        self.card4 = "IFIRST,ILAST".split(",")
        self.card5 = ["ASYM"]
        self.card5a = [] #TODO
        self.card5b = "ALPHA,RISE,NSUBUNITS,NSTARTS,STIFFNESS".split(",") # for H ASYM only
        # 6 - 12 for each dataset, terminate with RELMAG <=0
        self.card6 = "RELMAG,DSTEP,TARGET,THRESH,CS,AKV,TX,TY".split(",")
        self.card7 = "RREC,RMAX1,RMAX2,DFSTD,RBFACT".split(",")
        self.card8 = ["FINPAT1"]
        self.card9 = ["FINPAT2"]
        self.card10a = ["FINPAR"]
        self.card10b = "NIN,ABSMAGPIN,IFILMIN,DFMID1IN,DFMID2IN,ANGASTIN,MORE".split(",")
        self.card11 = ["FOUTPAR"]
        self.card12 = ["FOUTSH"]
        self.card13 = ["F3D"]
        self.card14 = ["FWEIGH"]
        self.card15 = ["MAP1"]
        self.card16 = ["MAP2"]
        self.card17 = ["FPHA"]
        self.card18 = ["FPOI"]
        self.set_default_params()

        self.set(params)
        self.workdir = "."

        self.exec_file = "frealign"
        self.cores = 16
        self.saves = []

    def run(self, project = None, server = None, stdout = None, background = False):
        from datetime import datetime
        import os
        if server is None:
            # run on local machine
            sr = FrealignScriptRunner(self)
            sr.workdir = self.workdir
            script_dir = self.workdir
            script_file = os.path.join(script_dir, "frealign_script_%s.csh" % datetime.now().strftime("%d_%m_%y_%H%M%S"))
            sr.script = script_file
            self.write_frealign_input_file(script_file)
            sr.run(stdout = stdout, background = True)
            if background:
                return sr
        self.cleanup()

    def cleanup(self):
        '''
            clean up the files
        '''

        # remove temp directory
        if self.temp_dir is not None and os.path.exists(self.temp_dir) and self.temp_dir.startswith("/tmp/"):
            os.system('rm -rf %s' % self.temp_dir)

    def set_cores(self, ncores):
        self.cores = ncores

    def set_pixel_size(self, pixel_size):
        self.params["PSIZE"] = pixel_size
        for dataset in self.params["datasets"]:
            if dataset["RREC"] < 0:
                dataset["RREC"] = 2 * pixel_size

    def set_number_particles(self, num_ptcl):
        self.params["ILAST"] = num_ptcl

    def set(self, d):
        '''
            set parameters according to the input directory
        '''
        for key, value in d.items():
            if key in self.params:
                self.params[key] = value
            elif len(self.params["datasets"]) > 0 and key in self.params["datasets"][0]:
                self.params["datasets"][0][key] = value
            else:
                raise Exception, "No this key exists: %s" % key

    def get_str(self, value):
        '''
            get string representation of a FREALIGN_EXEC parameter value
        '''
        if value is False: return "F"
        if value is True: return "T"
        if type(value) == type(1): return "%d" % value
        if type(value) == type(1.1): return "%.5f" % value
        if type(value) == type([]) or type(value) == type(()):
            return ",".join([self.get_str(v) for v in value])
        return value

    def get_card_str(self, card, params = None):
        if params is None: params = self.params
        if type(card) == type(""): # this is the str of card prop. get card first
            card = getattr(self, card)
        return ",".join([self.get_str(params[key]) for key in card])


    def get_card_str_list(self):
        card_strs = []
        card_num = 1
        while card_num < 19:

            # loop the cards 6 to 12 for all datasets
            if card_num == 6:
                for dataset in self.params["datasets"]:
                    # write 6-12 cards
                    for inner_card_num in range(6, 13):
                        if inner_card_num == 10:
                            if "FINPAR" in dataset:
                                card_strs.append(self.get_card_str(self.card10a, dataset))
                            else:
                                for micrograph in self.params["micrographs"]:
                                    card_strs.append(self.get_card_str(self.card10b, micrograph))
                        else:
                            card_strs.append(self.get_card_str("card%d" % inner_card_num, dataset))

                # write card 6 for termination
                dataset = {}
                for key in self.card6:
                    dataset[key] = 0
                card_strs.append(self.get_card_str(self.card6, dataset))
                card_num = 13
                continue

            card_name = "card%d" % card_num
            card = getattr(self, card_name)
            card_strs.append(self.get_card_str(card))
            if card_num == 5:
                if self.params["ASYM"] == "H":
                    card_strs.append(self.get_card_str("card5b"))
                elif self.params["ASYM"] == "N": #TODO: 'N' should be check for integer
                    card_strs.append(self.get_card_str("card5a"))

            card_num += 1
        return card_strs

    def set_box_size(self, box_size = -1):
        if box_size == -1 or box_size is None: return
        if self.params["RO"] <= 0 and self.params["PSIZE"] > 0:
            self.params["RO"] = int(box_size * self.params["PSIZE"]  / 2 - 2)

    def set_particle_size(self, particle_size = -1):
        '''
            set particle size related parameters
        '''
        if particle_size <= 0 or particle_size is None: return

        self.params["RO"] =  int(particle_size * 1.5 / 2)

    def setup_result_file_names(self, output_root = None, temp_dir = None):
        '''
            set up file names. if the file not in the saves list,
            we just put it into the temp dir and remove later
        '''
        if self.temp_dir is None:
            import tempfile
            self.temp_dir = tempfile.mkdtemp()
        if output_root is None:
            output_root = self.output_root
        output_root_bname = os.path.basename(output_root)
        d = {}
        fids = ["f3d", "fweigh", "fpha", "fpoi", "map1", "map2"]
        fids_d = ["foutpar", "finpat2", "foutsh"]
        for fid in fids:
            if fid not in self.saves:
                d[fid.upper()] = os.path.join(self.temp_dir, "%s_%s" % (output_root_bname, fid))
            else:
                d[fid.upper()] = "%s_%s" % (output_root, fid)
        return d

    def setup_dataset_filenames(self, output_root = None, temp_dir = None):
        '''
            set up dataset file names. if the file not in the saves list,
            we just put it into the temp dir and remove later
        '''
        if self.temp_dir is None:
            import tempfile
            self.temp_dir = tempfile.mkdtemp()
        if output_root is None:
            output_root = self.output_root
        output_root_bname = os.path.basename(output_root)
        d = {}
        fids_d = ["foutpar", "finpat2", "foutsh"]
        for dataset in self.params["datasets"]:
            inpar = dataset["FINPAR"]
            ibname = os.path.basename(os.path.splitext(inpar)[0])
            for fid in fids_d:
                fname = dataset[fid.upper()]
                if not fname:
                    fname = "%s_%s" % (ibname, )
                if fid not in self.saves:
                    d[fid.upper()] = os.path.join(self.temp_dir, "%s_%s" % (output_root_bname, fid))
                else:
                    d[fid.upper()] = "%s_%s" % (output_root, fid)


    def set_save(self,*args):
        for fid in args:
            if fid.lower() not in self.saves:
                self.saves.append(fid.lower())

    def set_nosave(self, *args):
        for fid in args:
            if fid.lower() in self.saves:
                self.saves.remove(fid.lower())

    def set_exec(self, exec_file):
        self.exec_file = exec_file


    def check_params(self):
        '''
            check parameters

        '''
        for dataset in self.params["datasets"]:
            dataset["FINPAT1"]

    def guess_stack_type(self, stack_fname):
        if stack_fname.endswith(".hed") or stack_fname.endswith(".img"):
            return "I"
        if stack_fname.endswith(".spi"):
            return "S"
        return "M" # "MRC" default

    def write_frealign_input_file(self, input_file_name):
        '''
            Write frealign run script
            :param str input_file_name: The script name to write
        '''
        self.check_params()
        f = open(input_file_name, 'w')
        f.write("#!/bin/csh\n\n")

        f.write("cd %s\n" % os.path.join(os.getcwd(), self.workdir))
        f.write("setenv OMP_NUM_THREADS %d\n" % self.cores)
        f.write("%s << EOF\n" % self.exec_file)
        f.write("\n".join(self.get_card_str_list()))
        f.write("\nEOF\n")
        f.close()
        print open(input_file_name).read()

    def create_tempdir(self, parentdir = None):
        import tempfile
        return tempfile.mkdtemp(dir=parentdir)

    def create_resultdir(self, resultdir):
        import os
        if os.path.exists(resultdir): return
        os.makedirs(resultdir)

    def set_default_params(self):
        if self.mp:
            self.exec_file = FREALIGN_MP_EXEC
        else:
            self.exec_file = FREALIGN_EXEC

        self.params = {
                    "CFORM" : "I", # I: Imagic, S: spider, M: mrc
                    "IFLAG" : 0,  # 0:reconstruct, 1: local refine, 3: global refine, 4: refine and reconst
                    "FMAG"  : False, # magnification refine
                    "FDEF"  : False, # defocus Refinement
                    "FASTIG" : False, # Astigmatism refinement
                    "FPART" :  False, #Defocus refinement for individual particles if FPART=T, otherwise
                                #defocus change is constrained to be the same for all
                                #particles in one image
                    "IEWALD" : 0, # 0 = No correction
                    "FBEAUT" : False, # Apply extra real space symmetry averaging and masking to
                                        #beautify final map just prior to output.
                    "FFILT"  : False, #Apply single particle Wiener filter to final reconstruction
                    "FCREF"  : False, #  Apply FOM filter to final reconstruction using function SQRT(2.0*FSC/(1.0+FSC)) (see publication #4 above).
                    "FBFACT" : False, # Determine and apply B-factor to final reconstruction
                    "FMATCH" : False, # Write out matching projections after the refinement

                    "IFSC" : 0, # Calculation of FSC tabel. 0 = Internally calculate two reconstructions with odd and even
                                    # numbered particles and generate FSC table at the end of the run.
                    "FDUMP" : False, #If set to T, dumps intermediate files from a 3D reconstruction and then terminates run
                    "IMEM"  : False, #  Memory usage: 0 = least memory, 3 = most memory. v9 only
                    "FSTAT" : False, # Calculate additional statistics in resolution table at the end, v8 only
                    "IBLOW" : 1, # Padding factor for reference structure, v8 only
                    "INTERP" : 1, # Interpolation scheme used for 3D reconstruction:
                    # card 2
                    "RO" : -1, # Outer radius of reconstruction in Angstroms from centre of particle,
                    "RI" : 0, # Inner radius of reconstruction in Angstroms from centre of particle
                    "PSIZE" : -1, # Required pixel size [Angstrom],
                    "MW" : -1, # Approximate molecular mass of the partcle, in kDa.
                    "WGH" : 0.07, # % Amplitude contrast (-1...1): 0.07
                    "XSTD" : 0.0, #  number of standard deviations above mean for masking of input low-pass filtered 3D model
                    "PBC" : 1000, # Phase residual / pseudo-B-factor conversion Constant: 5.0. W = exp (-DELTAP/PBC * R^2)
                    "BOFF" : 0.0, # average phase residual: 60.0, approximate average phase residual of all particles, used in calculating weights for contributions of different  particles to 3D map (see Grigorieff, 1998).
                    "DANG" : 30, # angular step size for the angular search used in modes IFLAG=3,4,
                    "ITMAX" : 50, # number of cycles of randomised search/refinement used in modes IFLAG=2,4
                    "IPMAX" : 10, # number of potential matches in a search that should be tested further in a subsequent local refinement.

                    # card 3
                    "PMASK" : [1, 1, 1, 1, 1],  #  - 0/1 mask to exclude parameters from refinement.
                    "DMASK" : "",

                    # card 4
                    "IFIRST" : 1, # First and last particle to be included: 1,5000
                    "ILAST" : -1,

                    # card 5
                    "ASYM" : "H",  #  symmetry required Cn,Dn,T,O,I,I1,I2 or N (can be zero), H

                    # card 6 - 12
                    "datasets" : [

                                  ],
                    # H ASYM
                    "ALPHA" : -1, # DPHI,
                    "RISE" : -1, # DP,
                    "NSUBUNITS" : 1, #
                    "NSTARTS" : 1, #
                    "STIFFNESS" : 0.0001, #

                    "F3D" : "F3D",
                    "FWEIGH" : "FWEIGH",
                    "MAP1" : "MAP1",
                    "MAP2" : "MAP2",
                    "FPHA" : "FPHA",
                    "FPOI" : "FPOI"
                    }

    def add_dataset(self, magnification = 1, dstep = 14, target = 90, thresh = 90, cs = 2., akv = 200., tx = 0., ty = 0.,
                    input_params = "",
                    rrec = -1, rmax1 = 200, rmin = 15,
                    dfstd = 1000, rbfact = 0, micrographs = [], input_particles = "", output_projection = "", output_param = "", output_shift = ""):
        dataset = {}
        dataset.update({
                        "RELMAG" : magnification, # Relative magnification of data set.
                        "DSTEP" : dstep, # Densitometer step size. 14 for K2?
                        "TARGET" : target, # Target phase residual (for resolution between RMAX1 and RMAX2)
                        "THRESH" : target, # Phase residual cut-off. Any particles with a higher overall phaseresidual will not be included in the reconstruction when IFLAG=0,1,2,3
                        "CS" : cs, #
                        "AKV" : akv, # High Tension
                        "TX" : tx, #  Beam tilt [mrad] in X, Y direction: 0.0, 0.0
                        "TY" : ty,
                        "FINPAR" : input_params,
                        "RREC" : rrec, # Resol. of reconstruction in Angstroms, e.g. 10.0
                        "RMAX1" : rmax1, # Resol. in refinement in Angstroms, low & high: 200.0,25.0
                        "RMAX2" : rmin,
                        "DFSTD" : dfstd, # Defocus uncertainty in Angstroms
                        "RBFACT" : rbfact, # B-factor to apply to particle image projections before orientation  determination or refinement.
                        "micrographs" : micrographs,
                        "FINPAT1" : input_particles,
                        "FINPAT2" : output_projection,
                        "FOUTPAR" : output_param,
                        "FOUTSH" : output_shift,

                    })

        self.params["datasets"].append(dataset)
class FrealignReconstruct(FrealignV8):
    '''
        Run A Reconstruction using FREALIGN_EXEC.
        Reconstruct only: set IFLAG = 0, FINPAR to the parameter file,
        Reconstruct needs:
        1. input particles
        2. input alignment file
        3. output root
        4. parameter dictionary
    '''
    def __init__(self, output_root, params):
        params["IFLAG"] = 0
        FrealignV8.__init__(self, params)

        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.set_save("f3d", "map1", "map2")
        self.output_root = output_root



        d = {
            }
        d.update(self.setup_result_file_names(output_root = output_root, temp_dir = self.temp_dir))
        self.set(d)
    def run(self, project = None, server = None, stdout = None, background = False):
        output_volume = self.params["F3D"]
        input_stack = self.params["datasets"][0]["FINPAT1"]
        # will create a new output volume with the same size of the input particle stack
        from EMAN2 import EMData, test_image
        data = EMData()
        data.read_image(input_stack, 0, True)
        nx = data.get_xsize()
        vol = test_image(1, size=(nx,nx,nx))
        if self.params["CFORM"].upper() == "I":
            ext = "hed"
        elif self.params["CFORM"].upper() == "S":
            ext = "spi"
        elif self.params["CFORM"].upper() == "M":
            ext = "mrc"
        print "%s.%s" % (output_volume, ext)
        vol.write_image("%s.%s" % (output_volume, ext), 0)
        FrealignV8.run(self, project, server, stdout, background)

class FrealignRefineLocal(FrealignV8):

    '''
        Run an alignment using FREALIGN_EXEC.
        alignment only: set IFLAG = 1, FINPAR to the input parameter file,
        alignment needs:
        1. input particles
        2. input alignment file
        3. output root
        4. parameter dictionary
    '''
    def __init__(self, input_particles, input_alignment, output_root, params):
        params["IFLAG"] = 1
        FrealignV8.__init__(self, params)

        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.set_save("foutpar")
        self.output_root = output_root
        self.setup_file_names()

        d = {"FINPAR" : input_alignment,
            }
        d.update(self.setup_file_names())
        self.set(d)


class FrealignReconstructMP(FrealignV8):
    '''
        Use multiple process do the reconstruction and merge together
    '''

    def __init__(self, input_particles,input_alignment, output_root, params, nprocs = 1, ppn = 1, version = 9):
        '''
            :param str input_particles: the input particle stack
            :param str input_alignment: the input parameters file. The .par file
            :param str output_root: The output root name. %s_foutpar, %s_f3d.???,...
            :param dict params: The parameters inputs for the refinement.
            :param int nprocs: number of reconstruction instances
            :param int ppn: number of cpu use per reconstruct instance
        '''

        self.nprocs = nprocs
        self.ppn = ppn
        if version < 9: raise Exception, "Multi reconstruction only support from frealign version 9"
        FrealignV8.__init__(self, params, version = version)

    def run(self):
        '''
            create an instance of FrealignV8 Reconstruct instance and run parallel. Save partial results and merge after all recosntruct instance finished

        '''

        from copy import copy
        params = copy(self.params)
        params['FDUMP'] = True
        # we split the particles to equal numbers for each procs
        nptcls = EMUtil.get_image_count(self.input_particles)
        if nptcls == 1:
            data = EMData()
            data.read_image(self.input_particles, 0, True)
            nptcls = data.get_zsize()
        nptcls_per_proc = int(nptcls / self.nprocs) + 1
        srs = []
        for i in range(self.nprocs):
            params_current = copy(params)

            ifirst = i * nptcls_per_proc + 1
            ilast = i * nptcls_per_proc
            if ilast < nptcls: ilast = nptcls
            params_current['IFIRST'] = ifirst
            params_current['ILAST'] = ilast

            # set the output_volume
            params_current['F3D'] = 'intermidate_volume_f3d_%d' % ()

            fr = FrealignReconstruct(self.input_particles, self.input_alignment,
                                     self.output_root, params_current)
            sr = fr.run()
            srs.append(sr)

        # waiting for all instance finish
        for sr in srs:
            sr.join()

        # merge the volumes using "merge_3d"

        #merge_volume()


def get_params(params):
    '''
        get parameters from params and return the params for frealign
    '''
    pass

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
    import argparse, os

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
        fr = FrealignReconstruct(os.path.splitext(options.params)[0], d)
        fr.add_dataset(input_params = os.path.join(os.getcwd(), input_params),
                       input_particles = options.ptcls,
                       cs = 2.7, akv = 300.0,
                       )
        fr.set_save("reconstruct", "fsc1", "fsc2")
        fr.workdir = "."
        fr.set_pixel_size(options.apix)
        fr.set_cores(options.cores)
        if options.frealign_exec is not None:
            fr.set_exec(options.frealign_exec)

        #fr.set(d)
        from datetime import datetime
        fr.run(stdout = open('frealign_log_%s.log' % datetime.now(), 'w'))
    elif options.task == "refine":
        pass
