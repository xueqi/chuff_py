#!/bin/env python

import os
from matplotlib import pyplot as plt
import numpy
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--frealign_file', default= None)
    parser.add_argument('--box_list_file', default = None)
    parser.add_argument('--guessed_helical_twist', default = None, type=float)
    parser.add_argument('--graph_dir', default = None)
    parser.add_argument('--pres_histogram_bins', default = 20, type=int)
    parser.add_argument('--phi_histogram_bins', default = 10, type=int)
    parser.add_argument('--yrange', default = 30, type=int)
    parser.add_argument('--outlier_magnitude', default = 10, type=float)
    parser.add_argument('--max_phi_stdev', default = 1.3, type=float)
    options = parser.parse_args()
    
    #TODO: read helical twist from somewhere
    helical_twist = None
    if options.frealign_file is None:
        raise Exception, 'ERROR: need to specify frealign info file ("--frealign_file=<xxx>/header_5.par")'
    box_list = None
    if options.box_list_file is None:
        print "Warning: the box_list_file is not supplied. Will not print the filament name on graph"
    else:
        box_list = get_box_list(options.box_list_file)

    if options.guessed_helical_twist is None:
        options.guessed_helical_twist = get_helical_twist()
    if options.graph_dir is None:
        frealign_dir = os.path.dirname(options.frealign_file)
        graph_dir = "%s_graphs" % frealign_dir
    else:
        graph_dir = options.graph_dir
    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)

    params = read_frealign_params(options.frealign_file)

    filaments, phi_deviation, delta_repeat, delta_psis = graph_frealign(params, output_dir = graph_dir, helical_twist = options.guessed_helical_twist)
    pres = [param[11] for param in params]

    n, bins, patches = plt.hist(pres, options.pres_histogram_bins)
    plt.savefig("%s.png" % os.path.join(graph_dir, os.path.splitext(os.path.basename(options.frealign_file))[0]))
    

    # plot for each filament
    phi_stdevs = []
    phi_outliers = []
    for filament_num, fr in filaments:
        phi_devs = phi_deviation[fr[0]:fr[1]]
        phi_stdev = numpy.std(phi_devs)
        phi_stdevs.append(phi_stdev)
        if box_list is not None:
            plot_title = os.path.splitext(os.path.basename(box_list[int(filament_num) - 1]))[0]
            plot_save_name = os.path.join(graph_dir, plot_title)
        else:
            plot_title = "filament_%s" % filament_num
            plot_save_name = os.path.join(graph_dir, "filament_%s" % filament_num)
        print plot_title
        theta_column = 2
        pres_column = 11
        dpsis = delta_psis[fr[0]:fr[1]]
        press = [param[pres_column] for param in params[fr[0]:fr[1]]]
        dthetas = [90 - param[theta_column] for param in params[fr[0]:fr[1]]]
        drepeats = delta_repeat[fr[0]:fr[1]]
        xs = range(fr[1] - fr[0])
        xss = [param[4] for param in params[fr[0]:fr[1]]]
        yss = [param[5] for param in params[fr[0]:fr[1]]]

        plt.clf()
        fig, ax1 = plt.subplots()
        ax1.plot(xs, phi_devs, label="phi dev")
        ax1.plot(xs, dthetas, label = "90 - theta")
        ax1.plot(xs, dpsis, label = "delta_psi")
        ax1.plot(xs, drepeats, label = "delta_repeats")
        ax1.plot(xs, xss, label = "x shift")
        ax1.plot(xs, yss, label = "y shift")
        ax1.legend(loc=0)
        ax1.set_ylim(-20,20)
        ax2 = ax1.twinx()
        ax2.plot(xs, press, '--.',label = "Phase residual")
        ax2.legend(loc=0)
        max_outlier = options.outlier_magnitude
        n_outliers = len(filter(lambda x: abs(x) > max_outlier, phi_devs))
        phi_outlier = (100 * n_outliers) / len(phi_devs)
        phi_outliers.append(phi_outlier)

        plt.title("%s phi stdev: %.1f, outlier: %d" % (plot_title, phi_stdev, phi_outlier))
        plt.show()
        print plot_save_name
        plt.savefig("%s.png" % plot_save_name)
        break
        os.system('convert %s.png %s.jpg' % (plot_save_name, plot_save_name))
    # histogram of phi stdevs
    plt.clf()
    n, bins, patches = plt.hist(phi_stdevs)
    plt.savefig("%s_stdev_hist.png" % os.path.join(graph_dir, "phi_stats"))
    # histogram of phi outliers
    plt.clf()
    n, bins, patches = plt.hist(phi_outliers)
    plt.savefig("%s_outliers_hist.png" % os.path.join(graph_dir, "phi_sttts"))

def graph_frealign(params, output_dir = None, helical_twist = None):
    '''
        :params list params: parameters read from frealign output file, 
        :params str output_dir: output directory
        :params float helical_twist: The helical twist to predict phi
        :return: list of filament number and start, list of phi_deviation and list of delta_repeat
    '''
    phi_column = 3
    psi_column = 1
    filament_column = 7
    phi_deviation = [0] * len(params)
    delta_repeat = [0] * len(params)
    delta_psis = [0] * len(params)
    filament_range = [(params[0][filament_column], [0, 1])]
    first_psi = params[0][psi_column]
    last_psi = first_psi
    for i in range(1, len(params)):
        if params[i][7] != filament_range[-1][0]:
            filament_range.append((params[i][filament_column], [i, i+1]))
            first_psi = params[i][psi_column]
            last_psi = first_psi
            continue
        # deal psi
        filament_range[-1][1][1] = i
        psi = params[i][psi_column]
        dpsi = psi - last_psi
        if abs(dpsi) > 180:
            if psi > last_psi:
                psi -= 360
            else:
                psi += 360
        delta_psis[i] = psi - first_psi
        last_psi = psi
        # deal phi
        max_j = 4
        min_j = -4
        min_err = 10000;
        for k in range(-3 * 360, 3 * 360 + 1, 360):
            for j in range(min_j, max_j + 1):
                dphi = params[i][phi_column] - params[i - 1][phi_column] + k
                phi_dev_err = dphi - j * helical_twist
                if abs(phi_dev_err) < min_err:
                    min_err = abs(phi_dev_err)
                    phi_deviation[i] = phi_dev_err
                    delta_repeat[i] = j

    return filament_range, phi_deviation, delta_repeat, delta_psis
    

def read_frealign_params(param_file):
    '''
        read frealign params into array
    '''
    s = open(param_file).read().strip().split("\n")
    params = [[float(i) for i in line.strip().split()] for line in s if not line.strip().startswith("C")]
    return params

def get_box_list(box_list_file):
    return open(box_list_file).read().strip().split("\n")

def get_helical_twist():
    print "get helical twist yet not implemented"

if __name__ == "__main__":
    main()
