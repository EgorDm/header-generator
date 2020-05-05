#!/usr/bin/python3

################################################################################
# license
#
# license.py
# Written by Evan Wilde
# April 6 2014
#
# This program will place license agreement information at the top of source
# code files It reads your information from a config file, or requests your
# information to generate the config file
#
################################################################################

import argparse
import os
import re
import random
import math
import string
import pickle
import time


# File Property
#
# An object capable of returning contents of a file
#
class FileProperty:
    """docstring for fileProperty"""

    __file_name_pattern = re.compile("^.*/(.*)\.(.*)$")

    def __init__(self, filepath):
        """Creates a new file property"""
        self.__filepath = ""
        self.__filecreatetime = None
        self.__filepath = os.path.abspath(filepath)
        try:
            self.__filecreatetime = time.strftime("%b %d %Y",
                                                  time.localtime(
                                                      os.path.getctime(filepath)
                                                  )
                                                  )
        except Exception:
            pass

    def __eq__(self, other):
        """
        Determines if two files are the same
        Files are equal if the absolute filepath is the same.
        """
        return self.get_filepath() == other.get_filepath()

    def __hash__(self):
        """Hashing function for fileproperties
        This is the result of the python string hash function on the filepath"""
        return hash(self.__filepath)

    def __iter__(self):
        """Iterates through each line of the file"""
        f = self.open()
        if f:
            for line in f:
                yield line.strip('\n\r')
            f.close()
        else:
            yield ""

    def exists(self):
        """Returns if the file exists and is accessible"""
        try:
            f = open(self.__filepath)
            f.close()
            return True
        except IOError:
            return False

    def open(self, mode='r', buffering=-1, encoding=None, errors=None,
             newline=None, closefd=True, opener=None):
        """Returns an opened file"""
        try:
            return open(self.__filepath, mode, buffering, encoding, errors,
                        newline, closefd, opener)
        except IOError:
            print("Could not open file: %s" % self.__filepath)
            return None

    def get_lines(self):
        """returns all the lines in the file"""
        f = self.open()
        if f:
            for line in f:
                yield str.strip(line)
            f.close()
        else:
            yield ""

    def get_filepath(self):
        """Returns the absolute filepath"""
        return self.__filepath

    def get_filename(self):
        """Returns the filename without extension or path"""
        (filename, _) = self.__file_name_pattern.match(self.__filepath).groups()
        return filename

    def get_file(self):
        """Returns the filename and extension"""
        try:
            (filename, file_extension) = self.__file_name_pattern.match(
                self.__filepath).groups()
        except AttributeError:
            print("No file extension!")
        return filename + "." + file_extension

    def get_extension(self):
        """Returns the extension of the file"""
        try:
            (_, file_extension) = self.__file_name_pattern.match(
                self.__filepath).groups()
        except AttributeError:
            print("No file extension")
        return file_extension

    def get_ctime(self):
        """Returns last modified time of a file"""
        return self.__filecreatetime

    def set_file_pattern(self, pattern):
        """Sets the file search pattern for, allowing for different file patterns.
        If the pattern is unable to compile, it will revert to the previous
        pattern."""
        old_pattern = self.__file_name_pattern
        try:
            new_pattern = re.compile(pattern)
        except Exception:
            print("Error: Pattern Could Not Be Compiled")
            new_pattern = old_pattern
        self.__file_name_pattern = new_pattern

    def __str__(self):
        """String representation of the file data"""
        return str(self.get_file())

    def __repr__(self):
        """A pretty representation of the file data"""
        return str(self.get_file())


class Header:
    """Heading Data Container"""
    __username = ""
    __email = ""
    __file_data = None

    def __init__(self, username, email, filepath):
        """Create a new header object"""
        self.__username = username
        self.__email = email

        self.__file_data = FileProperty(filepath)

    def get_username(self):
        """Returns the name that will be applied to the source headers"""
        return self.__username

    def get_email(self):
        """Returns the email of the current user"""
        return self.__email

    def get_filepath(self):
        """Returns the absolute filepath"""
        return self.__file_data.get_filepath()

    def get_filename(self):
        """Returns the filename without extension or path"""
        return self.__file_data.get_filename()

    def get_file(self):
        """Returns the filename and extension"""
        return self.__file_data.get_file()

    def get_extension(self):
        """Returns the extension of the file"""
        return self.__file_data.get_extension()

    def get_create_time(self):
        """Returns the last modified time"""
        return self.__file_data.get_ctime()

    def __repr__(self):
        """A pretty representation of the header data"""
        return "{0} <{1}>\nFilename: {2} -- {4}\nExtension: {3}".format(
            self.__username, self.__email, self.get_filename(),
            self.get_extension(), self.get_create_time())


#################
# Regex patterns
#################
# --[Input File Patterns] ----------------------------
hidden_file_pattern = "^\.(.*)"
file_name_pattern = "^([a-zA-Z0-9_-]*)\.([a-zA-Z0-9]*)$"
hidden_file_pattern = re.compile(hidden_file_pattern)
file_name_pattern = re.compile(file_name_pattern)

# --[Template File Patterns] -------------------------
Template_Start_pattern = "---START"
Template_End_pattern = "---END"
Template_Type_pattern = "^TYPE:(.*)"
Template_Include_pattern = "^INCTYPE:(.*)"

Template_Type_pattern = re.compile(Template_Type_pattern)
Template_Include_pattern = re.compile(Template_Include_pattern)


def list_dir_visible(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


# Template
#
# Templates contains information on individual template files.
# This will include the metadata and the contents of the template.
class Template:
    """Contains the metadata for a template file
        The template is a hashable Object
    """

    def __init__(self, template_filename):
        """Initializes a template file"""
        self.include_pattern = ""
        self.type_associations = []
        self.template_file = FileProperty(template_filename)
        self.template_string = ""
        self.include_pos = False
        self.parse_template_file()

    def __eq__(self, other):
        """
        Template equality is defined by the file path
        TODO: Include file association in equality -- Maybe
        """
        return self.get_file() == other.get_file()

    def __hash__(self):
        """
        Hashing function for Templates
        Uses the hashing function for fileProperty
        """

        return hash(self.get_file())

    def __repr__(self):
        """
        Human readable representation of a template
        """
        return_string = self.template_file.get_file()
        #   if len(self.type_associations) > 0:
        #       return_string += ": "
        #       return_string += self.type_associations[0]
        #       for assoc in self.type_associations[1:]:
        #           return_string += ", " + assoc
        return return_string

    def __iter__(self):
        """
        Iterates through the lines of the template file
        """
        for line in self.template_file:
            yield line

    def parse_template_file(self):
        """
        Reads the contents of the template file and fills members of the class
        """
        intemplate = False
        done_template = False

        line_number = 0

        for line in self.template_file:
            line_number += 1

            if "--START" in line:
                intemplate = True
            elif "--END" in line and intemplate:
                intemplate = False
                done_template = True
            elif "--END" in line and not intemplate:
                print("Syntax Error: {0}:{1} -- In Template".format(
                    self.template_file, line_number))
            elif "<INC>" in line and not done_template:
                self.include_pos = True
            elif "INCTYPE" in line:
                try:
                    (self.include_pattern,) = Template_Include_pattern.match(
                        line).groups()
                except AttributeError:
                    print("Syntax Error: {0}:{1} -- Include Type".format(
                        self.template_file, line_number))
            elif "TYPE" in line:
                try:
                    (type_assoc,) = Template_Type_pattern.match(line).groups()
                    self.type_associations.append(type_assoc)
                except AttributeError:
                    pass

    def is_include_top(self):
        """
        Returns true if include statements are before header
        """
        return self.include_pos

    def get_include(self):
        """
        Returns the include pattern
        i.e #include for c, import for python, etc...
        """
        return self.include_pattern

    def update_associations(self):
        """Unimplemented
        Updates the metadata headers for the template
        -- Deprecated, just use parse_template_file
        """
        pass

    def get_associations(self):
        """
        Returns the list of associated file types
        """
        return self.type_associations

    def get_file(self):
        """Returns the fileProperty of the Template"""
        return self.template_file

    def generate_header(self, header):
        """
        Returns a string form of the header with all the lables filled out
        """
        out_string = ""
        intemplate = False
        for line in self:
            if "--END" in line:
                intemplate = False
            elif intemplate:
                if "<FILE>" in line:
                    line = line.replace("<FILE>", header.get_filename())
                if "<FILEPATH>" in line:
                    line = line.replace("<FILEPATH>", header.get_filepath())
                if "<FILENAME>" in line:
                    line = line.replace("<FILENAME>", header.get_file())
                if "<USERNAME>" in line:
                    line = line.replace("<USERNAME>", header.get_username())
                if "<EMAIL>" in line:
                    line = line.replace("<EMAIL>", header.get_email())
                if "<DATE>" in line:
                    line = line.replace("<DATE>", header.get_create_time())
                out_string += line + "\n"
            elif "--START" in line:
                intemplate = True
        return out_string


# Template Manager
#
# Maintains the database of all the templates
class TemplateManager:
    """Template manager maintains the database of the installed templates and
       associated file extensions."""

    __filetype_registry = {}
    __registered_templates = []
    __template_location = ""
    __registry_updated = False

    def __init__(self, template_file_location):
        """Initializes the template manager and database"""
        self.__template_location = template_file_location
        self.load_registry_file()

    def get_registered_files(self):
        """Returns a list of registered fileProperty objects"""
        return [f.get_file() for f in self.__registered_templates]

    def get_registered_templates(self):
        """Returns a list of registered Template objects"""
        return [f for f in self.__registered_templates]

    def get_template_metadata(self, template_filename):
        """
        Reads the template metadata
        """
        # print ("DEBUG > getting template metadata")
        t = Template(self.__template_location + "/" + template_filename)
        if t.get_file().exists():
            self.__registered_templates.append(t)

            # print ("DEBUG > getting template metadata")

            for line in t.get_file():
                file_ext = Template_Type_pattern.match(line)
                if file_ext:
                    (file_ext,) = file_ext.groups()
                    self.__filetype_registry[file_ext] = t

    def get_new_templates(self):
        """
        Returns a list of unique templates that have been put in the template
        file but not registered with the database.
        """
        directory_files = []
        dir_files = list_dir_visible(self.__template_location)
        for fname in dir_files:
            directory_files.append(
                FileProperty(self.__template_location + "/" + fname))
        return list(set(directory_files) - set(self.get_registered_files()))

    def get_removed_templates(self):
        """
        Returns a list of unique templates that have been removed from the
        template file but not removed from the database
        """
        directory_templates = []
        # print("DEBUG > ", self.__template_location)
        dir_files = list_dir_visible(self.__template_location)
        for fname in dir_files:
            directory_templates.append(
                Template(self.__template_location + "/" + fname))
        return list(set(
            self.get_registered_templates()) - set(directory_templates))

    def get_modified_templates(self):
        """Unimplemented
        Returns a list of unique templates that have been modified, since
        their last update in the registry
        """
        directory_files = []
        # dir_files = list_dir_visible(self.__template_location)

        updated_files = []
        for f in directory_files:
            for f2 in self.get_registered_files():
                print("Directory File: {0} -- {1}\t Registry File: {2} -- {3}".
                      format(f.get_file(), f.get_ctime(), f2.get_file(),
                             f.get_ctime()))
                if (f.get_filepath() == f2.get_filepath()):
                    print("Same Kind")
                if (f == f2) and (f.get_ctime != f2.get_ctime):
                    updated_files.append(f2)
        return updated_files

    def add_new_templates(self):
        """Unimplemented
        Registers all new templates with the registry
        """
        for new_template in self.get_new_templates():
            self.get_template_metadata(new_template.get_file())

    def remove_deleted_templates(self):
        """Unimplemented
        Removes deleted registered templates from the registry
        """
        for removed_template in self.get_removed_templates():
            if removed_template in self.__registered_templates:
                self.__registered_templates.remove(removed_template)
            for assoc in removed_template.get_associations():
                # print ("Associated To:", assoc)
                del self.__filetype_registry[assoc]

    def update_modified_templates(self):
        """Unimplemented
        Updates modified templates in the registry
        """
        # print("Modified Templates:", self.get_modified_templates())
        pass

    def create_registry_file(self):
        """
        Creates a new template registry database
        """
        for template_file in list_dir_visible(self.__template_location):
            self.get_template_metadata(template_file)
        self.write_registry_file()

    def update_registry_file(self):
        """Unimplemented
        Updates the template registry database
        Inserts new registry templates
        Removes deleted registry templates
        Updates modified registry templates
        """
        self.add_new_templates()
        self.remove_deleted_templates()
        self.update_modified_templates()
        self.write_registry_file()

    def load_registry_file(self):
        """
        Loads the contents of the registry into the class members
        """
        registry_location = self.__template_location + "/.file_types.db"
        try:
            contains_registry = ".file_types.db" in os.listdir(
                self.__template_location)
            # print ("DEBUG > Registry exists:", contains_registry)
        except IOError:
            print("Error: Template Folder Not Found")
            exit()

        if not contains_registry:
            # print ("DEBUG > Create Registry")
            self.create_registry_file()
        else:
            # Don't update the registry here, instead we will run the updates
            # when a template is not in our database
            # print ("DEBUG > Load Registry")
            registry_contents = pickle.load(open(registry_location, "rb"))
            self.__registered_templates = registry_contents[0]
            self.__filetype_registry = registry_contents[1]

    def search_templates(self, file_extension):
        """Finds the corresponding template file for a given extension"""
        try:
            t = self.__filetype_registry[file_extension]
            if t.get_file().exists():
                return t
            else:
                self.update_registry_file()
                self.__registry_updated = True
        except KeyError:
            if not self.__registry_updated:
                self.update_registry_file()
                self.__registry_updated = True
            else:
                return None
            try:
                return self.__filetype_registry[file_extension]
            except KeyError:
                return None

    def write_registry_file(self):
        """Writes registered templates to the registry"""
        registry_location = self.__template_location + "/.file_types.db"
        lst = []
        lst.append(self.__registered_templates)
        lst.append(self.__filetype_registry)
        registry_file = open(registry_location, "wb")
        pickle.dump(lst, registry_file)
        registry_file.close()


# String pattern
input_pattern = "username:(.*)email:(.*)"
input_pattern = re.compile(input_pattern)
email_pattern = "[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
email_pattern = re.compile(email_pattern)

HEADER = '\033[95m'
BLUE = '\033[34m'
GREEN = '\033[92m'
DEBUG = '\033[93m'
FAIL = '\033[91m'
END = '\033[0m'


# For generating tmp file names
def random_name_generator(size=4, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# For breaking the incoming list of threads into separate lists for
# multi-threading.
def filechunks(files, threads):
    return [files[i:i + math.ceil(len(files) / threads)]
            for i in range(0, len(files), math.ceil(len(files) / threads))]


# Chuncking thing....
# I don't think this is necessary anymore.
def chunks(l, n):
    if n < 1:
        n = 1
    return [l[i:i + n] for i in range(0, len(l), n)]


def get_username(args_list):
    '''Collect Username from user'''
    # print(args_list)
    try:
        if not args_list['username']:
            return input("Your name:")
        else:
            return args_list['username']
    except KeyError:
        return input("Your name:")


def get_email(args_list):
    '''Collect Valid email from user'''
    try:
        if (not args_list['email']):
            valid = False
            while not valid:
                myemail = input("Your Email:")
                if (email_pattern.match(myemail)):
                    valid = True
        else:
            valid = False
            myemail = args_list['email']
            if (email_pattern.match(myemail)):
                valid = True
            while not valid:
                myemail = input("Your Email:")
        return myemail
    except KeyError:
        valid = False
        while not valid:
            myemail = input("your Email:")
            if (email_pattern.match(myemail)):
                valid = True
        return myemail


def create_config(arg_list):
    username = get_username(arg_list)
    email = get_email(arg_list)
    template_location = arg_list['templates']

    if not template_location:
        template_location = os.path.dirname(__file__) + "/templates"
    f = open("./.license.config", mode="w")
    f.write("username:" + username + "email:" + email + "\n" +
            template_location)
    f.close()
    return (username, email, template_location)


def read_config(fileProperty, current_directory):
    f = open(fileProperty.get_filepath(), "r")
    if f:
        (username, email) = input_pattern.match(f.readline().strip()).groups()
        templates = current_directory + f.readline().strip()
        if templates == "":
            templates = "templates/"
        f.close()
        return (username, email, templates)
    else:
        print("Error: Config File was removed\nRe-run the program\
               to try again.")
        exit()


def is_root(directory):
    path = os.path.abspath(directory)
    if path == "/":
        return True
    else:
        return False


def main():
    args = argparse.ArgumentParser(description="Add headings to source files.")
    args.add_argument('files', nargs="+", help="List of files to add\ headings to.")
    args.add_argument('-u', '--username', help="Specify a user name to place in the headings.")
    args.add_argument('-e', '--email', help="Specify an email address for the user.")
    args.add_argument('-t', '--templates', help="Specify the directory containing the templates.")
    args.add_argument('--version', action="version", version="%(prog)s 1.1")
    args = vars(args.parse_args())

    filename = ".license.config"
    directory = "./"

    license_file = FileProperty(directory + filename)
    while not license_file.exists() and not is_root(directory):
        directory += "../"
        license_file = FileProperty(directory + filename)

    # license_file = files.fileProperty("./.license.config")

    # while not license_file.exists():
    #     license_file

    # Handle The config file first
    # No config file or user gave an email, we need to re-write

    # file_exist = False
    if not license_file.exists():
        # print("No Config File")
        (username, email, templates) = create_config(args)

    else:
        # Just read from the file
        # print("Config File Found")
        # file_exist = True
        (usernameT, emailT, templatesT) = read_config(license_file, directory)

        # print (usernameT, emailT, templatesT)

        # Check that arguments are consistent with config contents
        updated_args = {}
        update_file = False
        keep_email = True
        keep_username = True
        keep_template = True
        # Check the username replacement
        if args['username'] and str(usernameT) != str(args['username']):
            user_selection = input(
                "Would you like to replace username {0} with {1}? y(es)/c(urrent)/n(o) [n]:".format(usernameT,
                                                                                                    args['username']))
            if user_selection is "y":
                # When they want to replace
                update_file = True
                keep_username = False

                username = args['username']  # Use passed username
                updated_args['username'] = args['username']  # Save passes username

                # print("DEBUG > UPDATED ARGS: Replacement ", updated_args)

            elif user_selection is "c":
                # When they want to run for current

                username = args['username']  # Use passed username
                updated_args['username'] = usernameT  # Save original username

                # print("DEBUG > UPDATED ARGS: Current Use ", updated_args)

            else:
                # When they don't want to change anything
                username = usernameT  # Use file username
                updated_args['username'] = usernameT  # Save original username

                # print("DEBUG > UPDATED ARGS: ", updated_args)
        else:
            username = usernameT
            updated_args['username'] = username

        # Check the email replacement
        if args['email'] and str(emailT) != str(args['email']):
            user_selection = input(
                "Would you like to replace email {0} with {1}? y(es)/c(urrent)/n(o) [n]:".format(emailT, args['email']))
            if user_selection is "y":
                # When they want to replace
                update_file = True
                keep_email = False

                email = args['email']  # Use passed email
                updated_args['email'] = args['email']  # Save passes email

                # print("DEBUG > UPDATED ARGS: Replacement ", updated_args)

            elif user_selection is "c":
                # When they want to run for current
                email = args['email']  # Use passed email
                updated_args['email'] = emailT  # Save original email

                # print("DEBUG > UPDATED ARGS: Current Use ", updated_args)

            else:
                # When they don't want to change anything
                email = emailT  # Use file email
                updated_args['email'] = emailT  # Save original email

                # print("DEBUG > UPDATED ARGS: ", updated_args)
        else:
            email = emailT
            updated_args['email'] = email

        # Check the template replacement
        if args['templates'] and str(templatesT) != str(args['templates']):
            user_selection = input(
                "Would you like to replace templates {0} with {1}? y(es)/c(urrent)/n(o) [n]:".format(templatesT,
                                                                                                     args['templates']))
            if user_selection is "y":
                # When they want to replace
                update_file = True

                templates = args['templates']  # Use passed templates
                updated_args['templates'] = args['templates']
                # Save passes templates

                # print("DEBUG > UPDATED ARGS: Replacement ", updated_args)

            elif user_selection is "c":
                # When they want to run for current
                templates = args['templates']  # Use passed templates
                updated_args['templates'] = templatesT
                # Save original templates

                # print("DEBUG > UPDATED ARGS: Current Use ", updated_args)

            else:
                # When they don't want to change anything
                templates = templatesT  # Use file templates
                updated_args['templates'] = templatesT
                # Save original templates

                # print("DEBUG > UPDATED ARGS: ", updated_args)
        else:
            templates = templatesT
            updated_args['templates'] = templates

        if update_file:
            (usernameT, emailT, templatesT) = create_config(updated_args)
            if not keep_username:
                username = usernameT
            if not keep_email:
                email = emailT
            if not keep_template:
                templates = templatesT
    templates = TemplateManager(templates)

    file_list = list(set(args['files']))  # The list of non-duplicate files
    for src_file in file_list:
        heading = Header(username, email, src_file)
        template = templates.search_templates(heading.get_extension())
        if not template:
            templates.update_registry_file()
            template = templates.search_templates(heading.get_extension())
            if not template:
                print("Error: Template for", heading.get_extension(),
                      "not found")
                exit(1)
        # print ("DEBUG > ext: {0} template:
        # {1}".format(heading.get_extension(), template))
        head = template.generate_header(heading)

        # filename = src_file

        # Make the backup hidden
        tmp_name = "."
        tmp_name += random_name_generator()
        tmp_name += ".bak"

        template_include = template.get_include()

        header_written = False
        with open(src_file, 'r') as s:
            with open(tmp_name, 'w') as d:
                if not template.is_include_top():
                    d.write(head)
                    header_written = True
                    for line in s:
                        d.write(line)
                else:
                    for line in s:
                        if (template_include in line) or (line is
                                                          string.whitespace):
                            pass
                        elif not header_written:
                            d.write(head)
                            header_written = True
                        d.write(line)

        # Put the file back where it goes
        os.rename(tmp_name, src_file)
    # Disabled until threading figured out
    # max_threads = multiprocessing.cpu_count()
    # file_list = filechunks(args['files'], max_threads)

    # print(file_list)
    # print("Chunks: {0}, Chunk Size: {2} files: {1}".format(len(file_list),
    # len(args['files']), len(file_list[0])) )


if __name__ == '__main__':
    main()
