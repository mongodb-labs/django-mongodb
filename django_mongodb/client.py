import signal

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):

    executable_name = "mongosh"

    @classmethod
    def settings_to_cmd_args_env(cls, settings_dict, parameters):
        options = settings_dict.get("OPTIONS", {})
        uri = options.get("uri")
        args = [cls.executable_name]
        if not uri:
            host = settings_dict.get("HOST")
            port = settings_dict.get("PORT")
            if port and host:
                host += f":{port}"

            dbname = settings_dict.get("NAME", "")
            user = settings_dict.get("USER")
            passwd = settings_dict.get("PASSWORD")
            auth_database = options.get("authentication_database")
            auth_mechanism = options.get("authentication_mechanism")
            retry_writes = options.get("retry_writes")

            protocol = options.get("PROTOCOL", "mongodb")

            if user:
                args += ["--username", user]
            if passwd:
                args += ["--password", passwd]
            if auth_database:
                args += ["--authenticationDatabase", auth_database]
            if auth_mechanism:
                args += ["--authenticationMechanism", auth_mechanism]
            if retry_writes is not None:
                args += ["--retryWrites", str(bool(retry_writes)).lower()]
            if host:
                uri = f"{protocol}://{host}/{dbname}"

        if uri:
            args.append(uri)
        args += options.get("filenames", []) + parameters
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
