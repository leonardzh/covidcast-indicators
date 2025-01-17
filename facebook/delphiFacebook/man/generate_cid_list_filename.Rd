% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/weights.R
\name{generate_cid_list_filename}
\alias{generate_cid_list_filename}
\title{Create filename to output list of tokens.}
\usage{
generate_cid_list_filename(type_name, params, module_type)
}
\arguments{
\item{type_name}{character value used for naming the output file}

\item{params}{a named list; must contain entries "start_time" and "end_time".
These are used in constructing the file name.}

\item{module_type}{character value used to indicate module filtering, if any}
}
\description{
Create filename to output list of tokens.
}
