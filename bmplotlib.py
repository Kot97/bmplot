import os
import re
import argparse
import json
import logging

from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# TODO : requirements for output of Google benchmark
# names of benchmarks in data files must starts with BM_ and on select list they cant start with BM_

# TODO : documentation!

def clear_none(**kwargs):
    if kwargs.get("title") is None :
        kwargs.pop("title")
    if kwargs.get("unit") is None :
        kwargs.pop("unit")
    return kwargs

def plot(file : str, output_dir, *args, **kwargs):
    kwargs = clear_none(**kwargs)
    file_name, file_ext = os.path.splitext(file)
    with open(file, "r") as f:
        if file_ext == ".json":
            logging.debug("Start plotting {}".format(file))
            plot_json(json.load(f), output_dir + "/" + file_name.split("/")[-1], *args, **kwargs)
        # TODO : plot_xml

def select_plot(files : set, select : list, output_dir, *args, **kwargs):
    kwargs = clear_none(**kwargs)
    data_json = dict()
    d = list()
    for file in files:
        _, file_ext = os.path.splitext(file)
        with open(file, "r") as f:
            if file_ext == ".json":
                logging.debug("Start analizing {}".format(file))
                f_json = json.load(f)
                context = f_json["context"]        # context in last file is copied
                for i in f_json["benchmarks"]:
                    title = i["name"].split("/")[0][3:]
                    for reg in select:
                        if re.search(reg, title):
                            logging.debug("Add benchmark {}".format(title))
                            d.append(i)
                            break
            # TODO : plot_xml
    data_json["benchmarks"] = d
    data_json["context"] = context
    plot_title = kwargs.get("title", "selected_plot")
    plot_json(data_json, output_dir + "/" + plot_title, *args, **kwargs)


def plot_json(json_file, output_file, *args, **kwargs):
    plot_title = kwargs.get("title", (str(json_file["context"]["executable"]).split(".")[1][1:]))
    time_unit = "[" + kwargs.get("unit", json_file["benchmarks"][0]["time_unit"]) + "]"
    plt.ioff()

    ext = kwargs.get("ext", ".pdf")
    log = kwargs.get("log", False)

    d = defaultdict(list)
    for i in json_file["benchmarks"]:
        # TODO : plots not only for aggregates
        if i["aggregate_name"] != "mean":
            continue
        temp = i["name"].split("/")
        title = temp[0][3:]
        arg = float(temp[1])
        # TODO : when no real_time
        d[title].append((arg, float(i["real_time"]), float(i["cpu_time"])))

    # TODO : only one plot (real_time or cpu_time or sth else)
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()

    # TODO : support more ext
    if ext is "pdf":
        pp = PdfPages(output_file + ".pdf")

    def _set(ax):
        if log:
            ax.set(xlabel="size", xscale="log", yscale="log", ylabel="time " + time_unit)
        else:
            ax.set(xlabel="size", ylabel="time " + time_unit)

    for title in d:
        size = np.asarray([ x[0] for x in d[title] ])
        real_time = np.asarray([ x[1] for x in d[title] ])
        cpu_time = np.asarray([ x[2] for x in d[title] ])

        # TODO : customize labels

        fig1.suptitle(plot_title + "_real_time")
        _set(ax1)
        ax1.plot(size, real_time, label=title)

        fig2.suptitle(plot_title + "_cpu_time")
        _set(ax2)
        ax2.plot(size, cpu_time, label=title)

    ax1.legend()
    ax2.legend()
    if ext is "pdf":
        fig1.savefig(pp, format="pdf", bbox_inches="tight")
        fig2.savefig(pp, format="pdf", bbox_inches="tight")
        pp.close()
    # TODO : support more ext

class PathType(object):
    def __init__(self, exists=True, type='file', perm=None):
        """ exists:
                True: a path that does exist
                False: a path that does not exist, in a valid parent directory
                None: don't care
            type: file, dir, None, or a function returning True for valid paths
                None: don't care
            perm: required permissions for file/dir
                r: read, w: write, "rw": read and write, None: don't care
        """

        assert exists in (True, False, None)
        assert type in ('file', 'dir', None) or hasattr(type, '__call__')
        assert perm in (None, "r", "w", "rw")

        self._exists = exists
        self._type = type
        self._perm = perm

    def __call__(self, string):
        e = os.path.exists(string)
        if self._exists is True:
            if not e:
                raise argparse.ArgumentTypeError("path does not exist: '%s'" % string)

            if self._type is None:
                pass
            elif self._type == 'file':
                if not os.path.isfile(string):
                    raise argparse.ArgumentTypeError("path is not a file: '%s'" % string)
            elif self._type == 'dir':
                if not os.path.isdir(string):
                    raise argparse.ArgumentTypeError("path is not a directory: '%s'" % string)
            elif not self._type(string):
                raise argparse.ArgumentTypeError("path not valid: '%s'" % string)
        else:
            if self._exists == False and e:
                raise argparse.ArgumentTypeError("path exists: '%s'" % string)

            p = os.path.dirname(os.path.normpath(string)) or '.'
            if not os.path.isdir(p):
                raise argparse.ArgumentTypeError("parent path is not a directory: '%s'" % p)
            elif not os.path.exists(p):
                raise argparse.ArgumentTypeError("parent directory does not exist: '%s'" % p)

        if self._perm is not None:
            if self._perm == "r" and not os.access(string, os.R_OK):
                raise argparse.ArgumentTypeError("you don't have read permission")
            if self._perm == "w" and not os.access(string, os.W_OK):
                raise argparse.ArgumentTypeError("you don't have write permission")
            if self._perm == "rw" and not (os.access(string, os.R_OK) and os.access(string, os.W_OK)):
                raise argparse.ArgumentTypeError("you don't have read and write permissions")

        return string
    