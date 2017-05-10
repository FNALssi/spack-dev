# SpackDev Motivation

## Single-package development
A developer working with a single package needs to

1. Download the source code, usually from a version control system.

1. Determine the dependencies of the package.

1. Install missing packages.

1. Configure the package build system so that it can locate the dependent packages.

All of this can be accomplished manually, if tediously. Doing things manually allows the developer to, among other things:
1. Install the source wherever s/he sees fit.
1. Work on a package that may or may not already be installed on the system.
1. Use an IDE to work with the package.
1. Perform incremental builds, clean builds, etc., as he s/he sees fit.
1. Throw up his or her hands, delete the source directory, and start over.

_The developer takes all these things for granted._

## Multiple-package development
A developer may need to work with more than one package at a time. Doing so involves all the issues of single-package development. In addition:
1. Incremental builds of multiple packages are potentially complex and error-prone. Although single-package incremental builds have multiple common solutions, e.g., hand-written make files, autotools and CMake, there are no multiple-package build systems with similarly widespread adoption.
1. Developing multiple packages potentially requires re-building intermediate packages not under development. Consider the simplest case: A depends on B depends on C. If the developer is working on A and C, s/he will also have to include B in order to propagate C's changes to A.

## Developing packages for Spack
Spack compiles packages in a very particular way. In particular, Spack uses compiler wrappers to pass extra flags to the compilers. Developers may need/want to understand how their packages behave when compiled by Spack.