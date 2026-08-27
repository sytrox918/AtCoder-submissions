import os
import time
import yaml
from datetime import datetime

from bs4 import BeautifulSoup
import requests

CONFIG_PATH = "config/config.yml"
PROBLEMS_API_ENDPOINT = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"

# Browser-like User-Agent to avoid CloudFront blocking
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Delay between page scrapes to avoid rate-limiting (seconds)
SCRAPE_DELAY = 1.5
# Number of retries for failed requests
MAX_RETRIES = 2
# Delay before retrying a failed request (seconds)
RETRY_DELAY = 5

EXTENSIONS = {
    "C++": "cpp",
    "Bash": "sh",
    "C#": "cs",
    "JavaScript": "js",
    "OpenJDK": "java",
    "Haskell": "hs",
    "OCaml": "ml",
    "Perl": "pl",
    "PHP": "php",
    "Python": "py",
    "PyPy": "py",
    "Pascal": "pas",
    "Perl": "pl",
    "Ruby": "rb",
    "Scala": "scala",
    "Text": "txt",
    "Visual Basic": "vb",
    "Objective-C": "m",
    "Swift": "swift",
    "Rust": "rs",
    "Sed": "sed",
    "Awk": "awk",
    "Brainfuck": "bf",
    "Standard ML": "ml",
    "Crystal": "cr",
    "Julia": "jl",
    "Octave": "m",
    "Nim": "nim",
    "TypeScript": "ts",
    "Perl6": "p6",
    "Kotlin": "kt",
    "COBOL": "cob",
    "C": ".c",
}


class AutoClone(object):
    """
    AtCoder AutoClone Class

    Attributes
    ----------
    user_id : str
        AtCoder user_id from yml file
    time_range : int
        range of time for submission query (seconds).
        e.g. : 3600 -> get submission of (current-3600 sec ~ current)
    cur_unix_time : int
        current unix time
    ac_only : bool
        flag whether to save non-ac code. this feature is currently disabled
    submissions : list of dict
        request result from AtCoder Problems Submission API
    session : requests.Session
        HTTP session with proper headers to avoid CloudFront blocking
    """

    def __init__(self, time_range):
        self.user_id = self.load_yml()["user_id"]
        self.time_range = time_range
        self.cur_unix_time = int(datetime.timestamp(datetime.now()))
        self.ac_only = True  # future todo

        # Create a session with browser-like headers to avoid CloudFront blocking
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

        if self.user_id is None:
            raise Exception("user_id not found. you must configure config/config.yml")

    def get_submissions(self) -> None:
        """
        Get submission information via AtCoder Problems API

        Returns
        -------
        submissions : dict
        """
        unix_time = self.cur_unix_time - self.time_range
        params = {"user": self.user_id, "from_second": unix_time}
        result = self.session.get(url=PROBLEMS_API_ENDPOINT, params=params)

        if not result.status_code == 200:
            raise Exception(f"{result.status_code} : Something went wrong")
        self.submissions = result.json()

    def get_and_write_submitted_codes(self) -> None:
        """
        Scrape AtCoder's submission pages to get codes
        & save write codes as new file
        """
        for i, record in enumerate(self.submissions):
            contest_id = record["contest_id"]
            language = record["language"]
            problem_id = record["problem_id"]
            submission_id = record["id"]
            result = record["result"]

            if self.ac_only and result == "AC":
                code = self.get_code(contest_id, submission_id)
                if code is not None:
                    self.write_code(code, contest_id, problem_id, language)
                    print(f"  ✓ Saved {contest_id}/{problem_id}")
                else:
                    print(f"  ✗ Failed to fetch {contest_id}/{problem_id} (submission {submission_id}), skipping")
            else:
                # Accept non-AC reuslt
                # Currently Unavailable
                pass

            # Delay between scrapes to avoid rate-limiting
            if i < len(self.submissions) - 1:
                time.sleep(SCRAPE_DELAY)

    def __call__(self):
        """
        Excecute AutoClone
        """
        self.get_submissions()
        print(f"Found {len(self.submissions)} submissions for user '{self.user_id}'")
        self.get_and_write_submitted_codes()

    def get_code(self, contest_id: str, submission_id: int) -> str:
        """
        Get code from AtCoder page

        Parameters
        ----------
        contest_id : str
            target contest_id
        submission_id : int
            target submissio_id

        Returns
        -------
        str or None
            str of raw code without extension, or None if fetch failed
        """
        submission_url = (
            f"https://atcoder.jp/contests/{contest_id}/submissions/{submission_id}"
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.session.get(submission_url, timeout=30)

                if response.status_code != 200:
                    print(f"    Warning: HTTP {response.status_code} for {submission_url}")
                    if attempt < MAX_RETRIES:
                        print(f"    Retrying in {RETRY_DELAY}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None

                soup = BeautifulSoup(response.content, "html.parser")

                # Use the #submission-code selector — this is the exact element
                # AtCoder uses for the source code
                code_element = soup.find("pre", id="submission-code")

                if code_element is None:
                    # Check if we got a CloudFront error page
                    if "cloudfront" in response.text.lower():
                        print(f"    Warning: CloudFront blocked request for {submission_url}")
                    else:
                        print(f"    Warning: Could not find #submission-code element on {submission_url}")

                    if attempt < MAX_RETRIES:
                        print(f"    Retrying in {RETRY_DELAY}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None

                return code_element.string

            except requests.RequestException as e:
                print(f"    Warning: Request error for {submission_url}: {e}")
                if attempt < MAX_RETRIES:
                    print(f"    Retrying in {RETRY_DELAY}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    continue
                return None

        return None

    @staticmethod
    def write_code(code, contest_id, problem_id, language) -> None:
        """
        Write code as new file

        Parameter
        ---------
        code : str
            str of raw code without extension
        contest_id : str
            target contest_id. used as folder name
        problem_id : str
            target problem_id. used as file name
        language : str
            target programming language (not extension)
        """
        extension = AutoClone.get_extension(language)
        path = f"{contest_id}/{problem_id}.{extension}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(code)

    @staticmethod
    def load_yml() -> dict:
        """
        Load yml config file

        Returns
        -------
        config : dict
            dict of config file.
        """
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        return config

    @staticmethod
    def get_extension(language: str) -> str:
        """
        Get extension of specified programming language

        Parameters
        ----------
        language : str
            target programming language (not extension)

        Returns
        -------
        extension : str
            file extension of the target language
        """
        extension = None
        for lang in EXTENSIONS.keys():
            if lang in language:
                extension = EXTENSIONS[lang]
                break
        if extension is None:
            raise Exception(
                f"Extension for {language} did not found. Please contact @kuriyan1204 via GitHub"
            )
        return extension


if __name__ == "__main__":
    pass
