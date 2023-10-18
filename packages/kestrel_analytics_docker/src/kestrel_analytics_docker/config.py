DOCKER_IMAGE_PREFIX = "kestrel-analytics-"

VAR_FILE_SUFFIX = ".parquet.gz"

# folder for input data (Kestrel variables)
# input/argument variables will be 0.parquet.gz, 1.parquet.gz, 2.parquet.gz, etc. in the folder
INPUT_FOLDER = "input"

# folder for output data (Kestrel variables)
# output/returned variables will be 0.parquet.gz, 1.parquet.gz, 2.parquet.gz, etc. in the folder
OUTPUT_FOLDER = "output"

# folder for additional returned display information
# should be one and only one display file (arbitrary name) in the folder with suffix .html or .pickle (Python object)
DISP_FOLDER = "display"
