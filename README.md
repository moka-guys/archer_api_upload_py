# archer_api_upload_py v1.0.0

This repository contains the python script required for uploading fastq files and submitting job on Archer analysis platform, via the API.
All fastqs in given folder (except Undetermined fastq) are uploaded and analysis job is initiated. Uploading is re-tried up to 5 times for each fastq in case it fails. 

## Inputs
- folder path (string) - file path where all fastq files are located
- archer credential file (string) - file path for authentication password
- job name (string) - job name for archer analysis
- log path (string) - file path for log file

## Outputs
- logfile.txt - txt file containing the log for file uploading and job submission.
- It is expected that the submitted job starts running on Archer platform (https://synnovis.analysis.archerdx.com)

## Docker image

Build the docker and push to Docker hub by `make`
To run docker 
```
docker run -v /dummy_fastq/Data/Intensities/BaseCalls:/data -v /archer_python:/auth_file -v /archer_python:/log_dir <docker_image> --runfolder /data --cred_file /auth_file/adx_password.txt --log_dir /log_dir --job_name test1

