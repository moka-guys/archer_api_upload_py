# this script uploads all fastq files (except Undetermined)
# in a given folder to adx analysis platform and initiate
# job submission for downstream analysis
import os
import argparse
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# specify a v7 analysis server to connect to and protocol id
server = "https://synnovis.analysis.archerdx.com"
protocol_id = 2
# define log
logger = logging.getLogger(__name__)


def get_arguments() -> argparse.Namespace:
    """
    Uses argparse to define and handle command line input arguments
    Returns:
        argparse.Namespace (object): Contains the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=(
            "This is to upload fastq files and submit job on adx platform "
        )
        )
    parser.add_argument("--runfolder", type=str, required=True, help="run folder name")
    parser.add_argument("--cred_file", type=str, required=True, help="adx credential file")
    parser.add_argument("--log_dir", type=str, required=True, help="log file path")
    parser.add_argument("--job_name", type=str, required=True, help="job name for adx")
    return parser.parse_args()


def get_credential(cred_file) -> str:
    """get the application key for adx upload

    cred_file (str): txt file containing application key

    Returns:
        application_key (str): credential for adx
    """
    with open(cred_file, "r") as file:
        lines = file.readlines()
    application_key = lines[0].strip()

    return application_key


def get_log(log_dir, runfolder) -> None:
    """
    Setup for log file
    Returns:
        None
    """
    rf = os.path.basename(runfolder)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    log_file = os.path.join(log_dir, f"{rf}_archer_api_logfile.txt")
    file_handler = logging.FileHandler(log_file, mode='w')
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    # log for network connection
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.DEBUG)
    urllib3_logger.addHandler(console_handler)
    urllib3_logger.addHandler(file_handler)
    urllib3_logger.propagate = True


def upload_file(folder, application_key, server) -> list:
    """upload fastq files from a given folder onto server
       upload is re-tried up to 5 times if fails

    Args:
        runfolder (str): run folder to upload
        application_key (str): credential for adx
        server (str): server url

    Returns:
        samples (list): list of samples for job submission
    """

    pathslist = []
    endpoint = "file-uploads/"
    url = "{}/api/{}".format(server, endpoint)
    for filename in os.listdir(folder):
        if "Undetermined" not in filename and filename.lower().endswith(".fastq.gz"):
            logger.info(filename)
            file_path = os.path.abspath(os.path.join(folder, filename))
            files = [('file', (filename, open(file_path, "rb"), "application/octet-stream"))]
            logger.info(files)
            headers = {'Authorization': f'API-Key {application_key}'}
            retries = Retry(
                        total=5,
                        backoff_factor=1,
                        allowed_methods=["POST"]
                        )
            adapter = HTTPAdapter(max_retries=retries)
            session = requests.Session()
            session.mount("https://", adapter)
            response = session.request("POST", url,  headers=headers, files=files)
            if response.status_code == 200:
                respJSON = response.json()
                logger.info(respJSON)
                # Check if 'data' key exists in the response JSON
                if 'data' in respJSON:
                    allData = respJSON['data']
                    paths = allData['path']
                    pathslist.append(paths)
                    if respJSON['success']:
                        logger.info(f"{filename} was uploaded successfully to {paths}")
                    else:
                        logger.error(f"{filename} failed to upload")
                else:
                    logger.error("data not found in respJSON")
            else:
                logger.error(f"data key not found in response for file {filename}")

    # format the paths list into the samples list with the sequence_files key
    samples = [{"sequence_files": pathslist}]
    return samples


def submit_job(samples, job_name, application_key, protocol_id, server) -> None:
    """submit job for adx analysis

    Args:
        samples (list): list of samples for job submission
        job_name (str): job name for analysis
        application_key (str): credential for adx
        protocol_id (int): protocol id for analysis
        server (str): server url

    Returns:
        None
    """
    endpoint = "job-submission/protocols/{}/submit-job".format(protocol_id)
    url = "{}/api/{}".format(server, endpoint)

    payload = {
     "job_name": job_name,
     "samples": samples
    }
    logger.info(f"{payload}")
    headers = {'Authorization': f'API-Key {application_key}'}
    response = requests.request("POST", url, headers=headers, json=payload)
    logger.info(response.json())
    logger.info(f"response status for job submission {response.status_code}")


if __name__ == "__main__":
    parsed_args = get_arguments()
    get_log(parsed_args.log_dir, parsed_args.runfolder)
    application_key = get_credential(parsed_args.cred_file)
    samples = upload_file(parsed_args.runfolder, application_key, server)
    submit_job(samples, parsed_args.job_name,  application_key, protocol_id, server)
