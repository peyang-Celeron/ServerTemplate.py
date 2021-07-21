import gendoc
from command.command import CommandEntry
import shutil
import webbrowser
import os


class CommandDoc(CommandEntry):
    def getName(self):
        return "doc"

    def getAliases(self):
        return ["docs", "document"]

    def exec(self, args):
        if len(args) < 1:
            self.logger.error("main", "Arguments required.")
            self.logger.info("main", "all - Generate, deploy and open automatically.")
            self.logger.info("main", "open - Open docs with browser.")
            self.logger.info("main", "gen - Generate document.")
            self.logger.info("main", "deploy - Deploy html to server.")
            return

        if args[0] == "open":
            self.open()
        elif args[0] == "deploy":
            self.deploy()
        elif args[0] == "gen":
            self.gen()
        elif args[0] == "all":
            self.gen()
            self.deploy()
            self.open()
        else:
            self.logger.error("main", "Argument error.")

    def open(self):
        self.logger.info("Opening...")
        webbrowser.open("http://127.0.0.1:" + str(self.instance.config["system"]["bind"]["port"]) + "/docs.html")

    def deploy(self):
        self.logger.info("Deploying...")
        if os.path.exists("docs.html"):
            if not os.path.exists("resources/resource"):
                os.mkdir("resources/resource")
            shutil.move("docs.html", "resources/resource/docs.html")

    def gen(self):
        gendoc.gen()
        self.logger.info("Document generated successfully.")