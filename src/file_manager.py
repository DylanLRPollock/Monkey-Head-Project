import shutil


class FileManager:
    def move_file(self, src, dst):
        try:
            shutil.move(src, dst)
        except Exception as e:
            ErrorHandler().handle_exception(e)

    def read_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                return file.read()
        except Exception as e:
            ErrorHandler().handle_exception(e)
            return None

    def write_file(self, file_path, content):
        try:
            with open(file_path, "w") as file:
                file.write(content)
        except Exception as e:
            ErrorHandler().handle_exception(e)
