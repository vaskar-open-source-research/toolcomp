import difflib
import logging
import os
import time
import typing as t
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from pydantic import BaseModel
from requests.exceptions import HTTPError, Timeout
from sphere_engine import CompilersClientV4

from tools.code.constants import (
    SPHERE_ENGINE_COMPILERS_ENDPOINT,
    SPHERE_ENGINE_RESULT_STREAM_REFUSE_DECODE_SIZE,
    SPHERE_ENGINE_RESULT_STREAM_WARN_SIZE,
    SphereEngineSubmissionStatus,
)

logger = logging.getLogger(__name__)

# Define a custom type for clarity.
T = t.TypeVar("T")


class SphereEngineCompilerResult(BaseModel):
    # execution status
    status: SphereEngineSubmissionStatus
    # execution time [seconds]
    time: float
    # memory consumed by the program [kilobytes]
    memory: int

    # signal raised by the program
    signal: int
    # description of the raised signal
    signal_desc: str

    # source code
    source: str | bytes
    # input data
    input: t.Optional[str | bytes]
    # output data
    output: t.Optional[str | bytes]
    # compilation info
    cmpinfo: t.Optional[str | bytes]
    # error data
    error: t.Optional[str | bytes]


class SphereEngineCompilersSubmissionFuture(BaseModel):
    id: int
    _client: CompilersClientV4

    # submission info
    language: t.Optional[str] = None
    version: t.Optional[str] = None
    source: t.Optional[str] = None
    input: t.Optional[str] = None
    time_limit: t.Optional[int] = None
    memory_limit: t.Optional[int] = None

    # states
    executing: t.Optional[bool] = None
    status: t.Optional[SphereEngineSubmissionStatus] = None

    # results
    result: t.Optional[SphereEngineCompilerResult] = None

    def __init__(self, **data):
        super().__init__(**data)
        client = data.get("client", None)
        if not client:
            api_key = os.getenv("SPHERE_ENGINE_API_KEY")
            client = CompilersClientV4(api_key, endpoint=SPHERE_ENGINE_COMPILERS_ENDPOINT)
        self._client = client

    def _get_stream(self, steam_name: str, stream_info: t.Optional[t.Dict[str, str | int]] = None):
        if stream_info is None:
            return None
        url = stream_info["uri"]
        size = stream_info["size"]
        assert steam_name in ["source", "input", "output", "cmpinfo", "error"]
        logger.debug(f"Getting {steam_name} stream from {url} with size {size} bytes.")

        try:
            response = requests.get(url, stream=True, timeout=10)  # 10 seconds timeout
            response.raise_for_status()  # Raise exception for HTTP errors

        except HTTPError:
            logger.exception(f"HTTP error encountered when fetching {steam_name} stream: ")
        except Timeout:
            logger.exception(f"Timeout error encountered when fetching {steam_name} stream: ")
        except Exception:
            logger.exception(f"Error encountered when fetching {steam_name} stream: ")

        result_bytes = response.content

        if size >= SPHERE_ENGINE_RESULT_STREAM_REFUSE_DECODE_SIZE:
            # refuse to decode large streams
            logger.warning(
                f"Very Large stream detected (more than {SPHERE_ENGINE_RESULT_STREAM_REFUSE_DECODE_SIZE/1024/1024}MB): {size/1024/1024:.3f} MB "
            )
            return result_bytes

        if size >= SPHERE_ENGINE_RESULT_STREAM_WARN_SIZE:
            # raise a warning if the output is greater than SPHERE_ENGINE_RESULT_STREAM_WARN_SIZE
            logger.warning(
                f"Large stream detected (more than {SPHERE_ENGINE_RESULT_STREAM_WARN_SIZE/1024}KB): {size/1024:.3f} KB "
            )

        # for safety reason we will only decode output stream with utf8
        try:
            return result_bytes.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode {steam_name} stream with utf-8. Returning raw bytes.")
            return result_bytes

    def get(self):
        logger.debug(f"Getting submission with ID: {self.id}")
        raw_result = self._client.submissions.get(self.id)

        # backfill info if not provided
        if self.language is None:
            self.language = raw_result["compiler"]["name"]
        if self.version is None:
            self.version = raw_result["compiler"]["version"]["name"]
        # update status
        self.status = SphereEngineSubmissionStatus(raw_result["result"]["status"]["code"])
        self.executing = raw_result["executing"]

        if self.status.value > 10 and not self.executing:
            logger.debug(f"Submission {self.id} execution completed. Fetching results...")
            result = {}
            result["status"] = self.status
            result["time"] = raw_result["result"]["time"]
            result["memory"] = raw_result["result"]["memory"]
            result["signal"] = raw_result["result"]["signal"]
            result["signal_desc"] = raw_result["result"]["signal_desc"]

            # Prepare stream data for parallel fetching
            stream_names = ["source", "input", "output", "cmpinfo", "error"]
            stream_infos = {
                name: raw_result["result"]["streams"].get(name) for name in stream_names
            }
            # Fetch streams in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_stream = {
                    executor.submit(self._get_stream, name, info): name
                    for name, info in stream_infos.items()
                }
                for future in as_completed(future_to_stream):
                    stream_name = future_to_stream[future]
                    try:
                        result[stream_name] = future.result()
                    except Exception as exc:
                        logger.exception(
                            f"Exception occurred while fetching {stream_name} stream: {exc}"
                        )
                        result[stream_name] = None

            self.result = SphereEngineCompilerResult(**result)

        return self.result

    def get_until_done(self, pull_interval_ms: int = 500):
        if self.executing is None:
            # make sure we get the initial state for lazy initialization
            self.get()

        while self.executing:
            self.get()
            time.sleep(pull_interval_ms / 1000)
        return self.result


class SphereEngineCodeExecutor:
    def __init__(self, verbose: bool = False):
        api_key = os.getenv("SPHERE_ENGINE_API_KEY")
        self.client = CompilersClientV4(api_key, endpoint=SPHERE_ENGINE_COMPILERS_ENDPOINT)

        if verbose:
            logger.setLevel(logging.DEBUG)

        self._test_connection()
        self.languages = {}
        self._load_metadata()

    def _test_connection(self):
        try:
            assert (
                self.client.test().get("message", None)
                == "You can use Sphere Engine Compilers API."
            )
            logger.debug("Connected to Sphere Engine Compilers API.")
        except AssertionError:
            logger.error("Connection to Sphere Engine API failed.")
            raise ConnectionError("Failed to connect to Sphere Engine Compilers API.")

    def _load_metadata(self):
        logger.debug("Requesting compilers information from Sphere Engine...")
        items = self.client.compilers().get("items", [])

        for item in items:
            logger.debug(f"Compiler item: {item['name']} | {item['id']} | {item['versions']}")
            self.languages[item["name"]] = {"id": item["id"], "versions": item["versions"]}

    def _validate_language_version(self, language: str, version: t.Optional[str] = None):
        logger.debug(f'Validate language: "{language}" | version: "{version}"')
        if language not in self.available_languages:
            closest = difflib.get_close_matches(language, self.available_languages, n=1, cutoff=0.6)
            logger.debug(f"Available languages: {self.available_languages}")
            error_message = f'Language "{language}" not found.'
            error_message += "" if not closest else f' Did you mean "{closest[0]}"?'
            raise ValueError(error_message)

        if version is not None and version not in self.list_language_versions(language):
            closest = difflib.get_close_matches(
                version, self.list_language_versions(language), n=1, cutoff=0.6
            )
            logger.debug(
                f'Available versions for "{language}": {self.list_language_versions(language)}'
            )
            error_message = f'Version "{version}" not found for language "{language}".'
            error_message += "" if not closest else f' Did you mean "{closest[0]}"?'
            raise ValueError(error_message)

    def _get_language_id(self, language: str) -> int:
        logger.debug(f'Looking up language ID for "{language}"...')
        self._validate_language_version(language)
        return self.languages[language]["id"]

    def _get_version_id(self, language: str, version: str) -> int:
        logger.debug(f'Looking up version ID for "{language}" - "{version}"...')
        self._validate_language_version(language, version)
        for v in self.languages[language]["versions"]:
            if v["name"] == version:
                return v["id"]

    @property
    def available_languages(self) -> t.List[str]:
        return list(self.languages.keys())

    def list_language_versions(self, language: str) -> t.List[str]:
        self._validate_language_version(language)
        return [version["name"] for version in self.languages[language]["versions"]]

    def _submit(
        self,
        code: str,
        language: str,
        version: t.Optional[str] = None,
        input_data: t.Optional[str] = None,
        time_limit: t.Optional[int] = None,
        memory_limit: t.Optional[int] = None,
    ) -> SphereEngineCompilersSubmissionFuture:
        language_id = self._get_language_id(language)
        version_id = None
        if version is not None:
            version_id = self._get_version_id(language, version)

        logger.debug(f"Submitting code for execution: {language} - {version}")
        submission = self.client.submissions.create(
            source=code,
            compiler_id=language_id,
            _input=input_data,
            time_limit=time_limit,
            memory_limit=memory_limit,
            compiler_version_id=version_id,
        )
        return SphereEngineCompilersSubmissionFuture(
            id=submission["id"],
            client=self.client,
            language=language,
            version=version,
            source=code,
            input=input_data,
            time_limit=time_limit,
            memory_limit=memory_limit,
            executing=True,
        )

    def execute_sync(
        self,
        code: str,
        language: str,
        version: t.Optional[str] = None,
        input_data: t.Optional[str] = None,
        time_limit: t.Optional[int] = None,
        memory_limit: t.Optional[int] = None,
        pull_interval_ms: int = 250,
    ) -> SphereEngineCompilerResult:
        submission = self._submit(code, language, version, input_data, time_limit, memory_limit)
        return submission.get_until_done(pull_interval_ms)

    def execute_async(
        self,
        code: str,
        language: str,
        version: t.Optional[str] = None,
        input_data: t.Optional[str] = None,
        time_limit: t.Optional[int] = None,
        memory_limit: t.Optional[int] = None,
    ) -> SphereEngineCompilersSubmissionFuture:
        return self._submit(code, language, version, input_data, time_limit, memory_limit)

    def ensure_length(
        self, primary: t.List[T], *others: t.Optional[t.List[T]]
    ) -> t.List[t.Optional[t.List[T]]]:
        """Ensure all optional lists match the length of the primary list, filling with None if necessary."""
        length = len(primary)
        result = []
        for lst in others:
            if lst is not None:
                assert len(lst) == length, "All lists must have the same length"
                result.append(lst)
            else:
                result.append([None] * length)
        return result

    def batch_execute_async(
        self,
        codes: t.List[str],
        languages: t.List[str],
        versions: t.Optional[t.List[str]] = None,
        input_data: t.Optional[t.List[str]] = None,
        time_limits: t.Optional[t.List[int]] = None,
        memory_limits: t.Optional[t.List[int]] = None,
        max_worker: int = 10,
    ) -> t.List[SphereEngineCompilersSubmissionFuture]:
        assert len(codes) == len(languages), "Codes and languages lists must have the same length"
        versions, input_data, time_limits, memory_limits = self.ensure_length(
            codes, versions, input_data, time_limits, memory_limits
        )

        # parallel submit
        futures = []
        execute_futures = []
        with ThreadPoolExecutor(max_workers=max_worker) as executor:
            for code, lang, ver, inp, tlim, mlim in zip(
                codes, languages, versions, input_data, time_limits, memory_limits
            ):
                futures.append(executor.submit(self._submit, code, lang, ver, inp, tlim, mlim))
            for future in as_completed(futures):
                try:
                    execute_futures.append(future.result())
                except Exception as e:
                    logger.error(f"Error encountered while submitting code: {e}")
        return execute_futures

    def batch_get(
        self,
        futures: t.List[SphereEngineCompilersSubmissionFuture],
        pull_interval_ms: int = 250,
        max_worker: int = 10,
    ) -> t.List[SphereEngineCompilerResult]:
        # multi threaded get, make sure futures finish executing
        results = []
        execute_result = []
        with ThreadPoolExecutor(max_workers=max_worker) as executor:
            for future in futures:
                results.append(executor.submit(future.get_until_done, pull_interval_ms))
            for result in as_completed(results):
                try:
                    execute_result.append(result.result())
                except Exception as e:
                    logger.error(f"Error encountered while fetching results: {e}")
        return execute_result
