import signal

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = "mongosh"

    @classmethod
    def settings_to_cmd_args_env(cls, settings_dict, parameters):  # noqa: ARG003 parameters unused
        options = settings_dict.get("OPTIONS", {})
        args = [cls.executable_name]

        host = settings_dict["HOST"]
        port = settings_dict["PORT"]
        dbname = settings_dict["NAME"]
        user = settings_dict["USER"]
        passwd = settings_dict["PASSWORD"]
        auth_database = options.get("authSource")
        auth_mechanism = options.get("authMechanism")
        retry_writes = options.get("retryWrites")

        if host:
            args += ["--host", host]
        if port:
            args += ["--port", port]
        if user:
            args += ["--username", user]
        if passwd:
            args += ["--password", passwd]
        if auth_database:
            args += ["--authenticationDatabase", auth_database]
        if auth_mechanism:
            args += ["--authenticationMechanism", auth_mechanism]
        if retry_writes is not None:
            args += ["--retryWrites", str(retry_writes).lower()]

        args.append(dbname)

        return args, None

    def runshell(self, parameters):
        sigint_handler = signal.getsignal(signal.SIGINT)
        try:
            # Allow SIGINT to pass to mongo to abort queries.
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            super().runshell(parameters)
        finally:
            # Restore the original SIGINT handler.
            signal.signal(signal.SIGINT, sigint_handler)
