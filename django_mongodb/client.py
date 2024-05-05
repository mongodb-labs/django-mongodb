import signal

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = "mongosh"
    help_options = ("--help", "-h")

    @classmethod
    def settings_to_cmd_args_env(cls, settings_dict, parameters):
        options = settings_dict.get("OPTIONS", {})
        uri = options.get("uri")
        args = [cls.executable_name]
        if not uri:
            host = settings_dict["HOST"]
            port = settings_dict["PORT"]
            if port and host:
                host += f":{port}"

            dbname = settings_dict["NAME"]
            user = settings_dict["USER"]
            passwd = settings_dict["PASSWORD"]
            auth_database = options.get("authenticationDatabase")
            auth_mechanism = options.get("authenticationMechanism")
            retry_writes = options.get("retryWrites")
            protocol = options.get("protocol", "mongodb")

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
            if host:
                uri = f"{protocol}://{host}/{dbname}"
            elif dbname:
                uri = dbname

        if uri:
            args.append(uri)

        if parameters:
            if not any(param in cls.help_options for param in parameters):
                args.append("--shell")
            args += parameters
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
