####################################
# Machine parameters for 'chuff' scripts
####################################

filesync_pause = 120;                 # For weird troubles on our linux cluster, try waiting
                                      #  after job completion to make sure files are synced.
qsub = 1;
nodes = 1;
cores = 16;
max_cpus = 64;

operating_system_type =   'linux';    # Required for running the provided binary 
                                      #  executables (frealign, rmeasure, etc)
                                      # Available options are currently:
                                      #  'linux','linux32','OSX'

                                      # Alternatively, you can specify these programs 
                                      #  directly (see Section 2)

EMAN2DIR = /home/cvs2/programs/EMAN2; # For sxihrsr

####################################
# If your environment is special, or included executables with chuff
#   do not work, you may need chuff to recognize special program versions, 
#  which can be defined here.
####################################

# cosmask_prog = 'cosmask'

submfg_prog = 'submfg';      # imod software
dm2mrc_prog = 'dm2mrc';      # imod software
octave_prog =           '/home/cvs2/programs/octave-3.4.3_build/octave-3.4.3/bin/octave -q'
bimg_prog =             'bimg';                # BSOFT image conversion
bint_prog =             'bint';                # BSOFT image conversion
bop_prog =              'bop';                # BSOFT image conversion
# bcat_prog               bcat                # BSOFT image conversion
# bhead_prog              bhead               # BSOFT image header info

proc2d_prog =           'proc2d';              # EMAN image conversion
batchboxer_prog =       'batchboxer';          # EMAN image conversion
proc3d_prog =           'proc3d';              # EMAN image conversion
# spider_prog =           '/usr/local/cluster/software/builds/njc2/spider/19.04/spider/bin/spider_linux_mp_intel64';              # Can specify the spider executable command here
# ctffind3_prog           ctffind3.exe        # CTF estimation
# em2em_prog              em2em.e             # IMAGIC image conversion

# ctftilt_prog            ctftilt.exe         # CTF estimation
# rmeasure_prog           rmeasure.exe        # Resolution estimation
# bfactor_prog =         'bfactor'             # Resolution estimation
# diffmap_prog            diffmap             # Resolution estimation

####################################
# Normally you shouldn't mess with the below program definitions; if the ones included with
#  "chuff" don't work, you will need to get help!
####################################

# frealign_prog           frealign_v8_cclin.exe     # Disabled resolution-weighted comparisons, for noisy data
# frealign_mp_prog frealign_v8_mp_cclin.exe   # Multicore version of this
