####################################
# Parameters for reconstruction
# Notes: 
#  * On a given line here, text following the "#" is a comment
#  * You are required to define all the parameters listed in Section 1.
#  * Example values for a kinesin-microtubule dataset are included here.
#     However, if a given parameter is unlikely to be 
#     correct for a new, unrelated project, it is commented out.
#  * The leading "#" must be removed from all parameter listings in Section 1,
#     and correct values given.
####################################

####################################
# Section 1: Essential parameters (neglect at your own peril!)
####################################

# mt_pf_types 11 3 12 3 13 3 14 3 15 3 15 4  # For multi-reference alignment:
                                           #  list of no. pfs, no. starts 
                                           #  for every MT type to consider

filament_outer_radius =        200;    # Outer filament radius (Angstroms); needed for volume 
                                      #  dimension

helical_repeat_distance =       81.7;  # Helical repeat distance in Angstroms

invert_density =                1;    # 1 means don't invert micrograph density, -1 means invert;
                                      # Here's how to set invert_density: 
                                      #
                                      #    -> If your microtubule density appears *black* in the
                                      #        micrographs, invert_density should be 1.
                                      #       This corresponds to what you would see with a 
                                      #        CCD detector.
                                      #
                                      #    -> If your microtubule density appears *white* in the
                                      #        micrographs, invert_density should be -1.
                                      #       This corresponds to what you would see if you 
                                      #         looked at a film negative.
                                      #
                                      # If this is wrong, you will experience total failure 
                                      #   in the reference alignment.
                                      #   (note that the radon step for in-plane helix 
                                      #   alignment will still work). 
                                      # 
                                      # Explanation:
                                      #  In the "true" image (i.e. what a CCD gives) high 
                                      #   electron density will be darker,
                                      #   due to contrast inversion by the CTF.
                                      #  With film negatives ("invert_density = -1"), 
                                      #   high electron density is lighter,
                                      #   due to a second contrast inversion (the film 
                                      #   is a negative of the true image).

num_repeat_residues =        1229;    # Number of residues in the asymmetric unit, 
                                      #  if known; this enables more accurate masking 
                                      #  of the reference volumes via the '-gauss_mask'
                                      #  option, i.e. "chuff frealix -gauss_mask". 
                                      #  For microtubule-kinesin, the asymmetric unit 
                                      #  is tubulin dimer + kinesin ~ 440*2+349 (kin monomer)

target_magnification =         59562; # 2.666667/(81.7/30.4139)*60000; from eg5_hidec analysis
# target_magnification         58333    # Estimated magnification in the micrographs 
                                      #  (your best guess, need not be perfect)

scanner_pixel_size =           16;  # Pixel size of detector or CCD (micrometers); this 
                                      #  is 6.35 for Nikon Coolpix, or 16 for Gatan 4Kx4K
                                      #  or 5.0 for Gatan K2

spherical_aberration_constant = 2.0;   # Typical values: 2.0 (F30) 2.0 (CM12) 4.1 (JEOL4000) 
                                      #  3.1 (JEOL3100)

accelerating_voltage =         200;    # Microscope voltage, in kV

amplitude_contrast_ratio =    0.07;    # Least essential parameter; 0.1 may work equally well;
                                      #   can be estimated for your data from defocus 
                                      #  pairs by the method of:
                                      #   Toyoshima, C. & Unwin, N. Contrast transfer 
                                      #     for frozen-hydrated specimens: determination 
                                      #     from pairs of defocused images. 
                                      #          Ultramicroscopy 25, 279-292 (1988).

wedge_offset = 8.5                   # Adjusts the orientation of the "wedge" used to 
                                      #  rebuild the microtubule seam
