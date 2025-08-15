from enum import Enum

SPHERE_ENGINE_COMPILERS_ENDPOINT = "0c91c551.compilers.sphere-engine.com"
SPHERE_ENGINE_PROBLEMS_ENDPOINT = "0c91c551.problems.sphere-engine.com"
SPHERE_ENGINE_CONTAINERS_ENDPOINT = "0c91c551.containers.sphere-engine.com"

SPHERE_ENGINE_RESULT_STREAM_WARN_SIZE = 1024 * 15  # 15 KB
SPHERE_ENGINE_RESULT_STREAM_REFUSE_DECODE_SIZE = 1024 * 1024  # 1 MB


class SphereEngineSubmissionStatus(Enum):
    # Transient States
    # submission is waiting in the queue
    waiting = 0
    # program is being compiled (for compiled languages)
    compilation_1 = 1
    compilation_2 = 2
    # program is being executed
    execution = 3

    # Final States
    # the program could not be executed due to a compilation error
    compilation_error = 11
    # an error occurred while the program was running (e.g., division by zero)
    runtime_error = 12
    # the program exceeded the time limit
    time_limit_exceeded = 13
    # the program was executed correctly
    success = 15
    # the program exceeded the memory limit
    memory_limit_exceeded = 17
    # the program tried to call illegal system function
    illegal_system_call = 19
    # an unexpected error occurred on the Sphere Engine side try making the submission again and if this occurs again
    internal_error = 20
