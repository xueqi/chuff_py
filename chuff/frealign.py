#!/bin/env python
'''
    This is the frealign wrapper in python.
'''

from collections import OrderedDict
from chuff.script_runner import TcshScriptRunner

from chuff.includes.server_configs.program_settings import FREALIGN_EXEC, FREALIGN_MP_EXEC

class FrealignScriptRunner(TcshScriptRunner):
    def __init__(self, frealign, server = None):
        TcshScriptRunner.__init__(self, server)
        self.frealign = frealign

    def get_workdir(self):
        return self.workdir

class Frealign(object):

    '''
        Each FREALIGN_EXEC instance must set the following:
        RO, PSIZE, CFORM, ILAST,
        ALPHA, RISE,
        RELMAG, DSTEP,
        RREC,
        FINPART1,
    '''

    def __init__(self, params = {}):
        self.params = OrderedDict()
        self.exec_version = 8
        self.mp = True
        if self.exec_version == 8:
            self.card1 = "CFORM,IFLAG,FMAG,FDEF,FASTIG,FPART,IEWALD,FBEAUT,FCREF,FMATCH,IFSC,FSTAT,IBLOW".split(",")
            self.card2 = "RO,RI,PSIZE,WGH,XSTD,PBC,BOFF,DANG,ITMAX,IPMAX".split(",")
            self.card3 = ["PMASK"]
        elif self.exec_version == 9:
            self.card1 = "CFORM,IFLAG,FMAG,FDEF,FASTIG,FPART,IEWALD,FBEAUT,FFILT,FBFACT,FMATCH,IFSC,FDUMP,IMEM,INTERP".split(",")
            self.card3 = ["PMASK", "DMASK"]
            self.card2 = "RO,RI,PSIZE,MW,WGH,XSTD,PBC,BOFF,DANG,ITMAX,IPMAX".split(",")
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

    def run(self, project = None, server = None):
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
            sr.tmp_dir = self.workdir
            sr.run()

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
        for key, value in d.items():
            if key in self.params:
                self.params[key] = value
            elif key in self.params["datasets"][0]:
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
                elif self.params["ASYM"] == "N":
                    card_strs.append(self.get_card_str("card5a"))
                    #TODO: add card5a to the params

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



    def set_exec(self, exec_file):
        self.exec_file = exec_file

    def write_frealign_input_file(self, input_file_name):
        '''
            Write frealign run script
            :param str input_file_name: The script name to write
        '''
        f = open(input_file_name, 'w')
        f.write("#!/bin/csh\n\n")

        f.write("cd %s\n" % os.path.join(os.getcwd(), self.workdir))
        f.write("setenv OMP_NUM_THREADS %d\n" % self.cores)
        f.write("%s << EOF\n" % self.exec_file)
        f.write("\n".join(self.get_card_str_list()))
        f.write("\nEOF\n")
        f.close()
        print open(input_file_name).read()
    def set_default_params(self):
        if self.exec_version == 8:
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

                    # card 4
                    "IFIRST" : 1, # First and last particle to be included: 1,5000
                    "ILAST" : -1,

                    # card 5
                    "ASYM" : "H",  #  symmetry required Cn,Dn,T,O,I,I1,I2 or N (can be zero), H

                    # card 6 - 12
                    "datasets" : [
                                  {
                        "RELMAG" : 1, # Relative magnification of data set.
                        "DSTEP" : 14, # Densitometer step size. 14 for K2?
                        "TARGET" : 90, # Target phase residual (for resolution between RMAX1 and RMAX2)
                        "THRESH" : 90, # Phase residual cut-off. Any particles with a higher overall phaseresidual will not be included in the reconstruction when IFLAG=0,1,2,3
                        "CS" : 2.0, #
                        "AKV" : 200, # High Tension
                        "TX" : 0.0, #  Beam tilt [mrad] in X, Y direction: 0.0, 0.0
                        "TY" : 0.0,
                        "FINPAR" : "FINPAR",
                        "RREC" : -1, # Resol. of reconstruction in Angstroms, e.g. 10.0
                        "RMAX1" : 200, # Resol. in refinement in Angstroms, low & high: 200.0,25.0
                        "RMAX2" : 15,
                        "DFSTD" : 1000, # Defocus uncertainty in Angstroms
                        "RBFACT" : 0, # B-factor to apply to particle image projections before orientation  determination or refinement.
                        "micrographs" : [
#                                          {
#                             "NIN" : 1000, # number of particle images for this film,
#                             "ABSMAGPIN": -1, # real magnification for this film
#                             "IFILMIN" : -1, # film number for this film
#                             "DFMID1IN" : -1, # defocus and astigmatism for this film
#                             "DFMID2IN" : -1,
#                             "ANGASTIN" : -1,
#                             "MORE" : 0, # use '1' for more cards describing more particle images in this stack of images, '0' to terminate.
#                                             }
                                          ],
                        "FINPAT1" : "FINPART1",
                        "FINPAT2" : "FINPART2",
                        "FOUTPAR" : "FOUTPAR",
                        "FOUTSH" : "FOUTSH",

                    }
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
class FrealignReconstruct(Frealign):
    '''
        Run A Reconstruction using FREALIGN_EXEC.
        Reconstruct only: set IFLAG = 0, FINPAR to the parameter file,
        Reconstruct needs:
        1. input particles
        2. input alignment file
        3. output root
        4. parameter dictionary
    '''
    def __init__(self, input_particles, input_alignment, output_root, params):
        params["IFLAG"] = 0
        Frealign.__init__(self, params)

        import tempfile
        temp_dir = tempfile.mkdtemp()
        d = {"FINPAR" : input_alignment,
             "FOUTPAR" : os.path.join(temp_dir, "OUTPUT_PAR.par"),
             "F3D" : "%s" % output_root,
             "FWEIGH" : os.path.join(temp_dir, "OUTPUT_WEIGHT"),
             "FPHA" : os.path.join(temp_dir, "OUTPUT_FPHA"),
             "FPOI" : os.path.join(temp_dir, "OUTPUT_FPOI"),
             "MAP1" : os.path.join(temp_dir, "OUTPUT_FSC1"),
             "MAP2" : os.path.join(temp_dir, "OUTPUT_FSC2")
            }
        self.set(d)

class FrealignRefineLocal(Frealign):
    '''
        Local refinement for frealign.
    '''

    def __init__(self):
        Frealign.__init__(self)
        self.params["IFLAG"] = 1


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

    parser = argparse.ArgumentParser(description="Frealign commandline wrapper.\nUse: frealign.py --params=frealign_bin1_gold1/chuck_apomyoIb_201501_5.par --output_dir=frealign_bin1_gold1 --apix=4.35 --ptcls=frealign_bin1_gold1/frealign_image_stack.hed --dp=28.14 --dphi=167.1")

    parser.add_argument("--apix", type = float, default = 1.,
                        help = "Pixel size of the particles and the volume")
    parser.add_argument("--dp", type = float, default = 1.,
                        help = "helical rise of the filament")
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

    options = parser.parse_args()

    if options.task == "resize":
        if options.new_size is None or options.output_stack is None:
            raise Exception, "must provide new_size and output_stack option fo resizing"
        resize_stack(options.ptcls, options.output_stack, options.new_size)
        exit()

    #TODO: remove the comment below
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
    if options.rmax <= 0:
        ro = xsize / 2 - 1
    else:
        ro = options.rmax

    input_params = options.params
    output_root = os.path.join(options.output_dir, os.path.splitext(os.path.basename(input_params))[0])
    d = {
            "FINPAR" : os.path.join(os.getcwd(), input_params),
            "ILAST"  : n_ptcls,
            "RO" : ro,
            "RISE" : options.dp,
            "ALPHA" : options.dphi,
            "FINPAT1" : os.path.join(os.getcwd(), options.ptcls),
            "FINPAT2" : os.path.join(os.getcwd(), "%s_pj.hed" % os.path.splitext(input_params)[0]),
            "FOUTPAR" : os.path.join(os.getcwd(), "%s_out.par" % os.path.splitext(input_params)[0]),
            "FOUTSH" : os.path.join(os.getcwd(), "%s.shft" % os.path.splitext(input_params)[0]),
            "F3D" : os.path.join(os.getcwd(), os.path.splitext(input_params)[0]),
            "FWEIGH" : os.path.join(os.getcwd(), "%s.wgt" % os.path.splitext(input_params)[0]),
            "MAP1" : os.path.join(os.getcwd(), "%s_vol_fsc1" % os.path.splitext(input_params)[0]),
            "MAP2" : os.path.join(os.getcwd(), "%s_vol_fsc2" % os.path.splitext(input_params)[0]),
            "FPHA" : os.path.join(os.getcwd(), "%s_phasediffs" % os.path.splitext(input_params)[0]),
            "FPOI" : os.path.join(os.getcwd(), "%s_pointspread" % os.path.splitext(input_params)[0]),
            "CS" : 2.7,
            "AKV" : 300,
            }
    fr = FrealignReconstruct(options.ptcls, options.params, os.path.splitext(options.params)[0], d)
    fr.workdir = "."
    fr.set_pixel_size(options.apix)
    fr.set_cores(32)
    if options.frealign_exec is not None:
        fr.set_exec(options.frealign_exec)

    #fr.set(d)

    fr.run()
