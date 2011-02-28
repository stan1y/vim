#!/usr/bin/python
"""Script for vim plugins update"""

# ruby original - http://tammersaleh.com/posts/the-modern-vim-config-with-pathogen

from config     import Config
from dircache   import opendir
from os         import chmod, listdir, makedirs, remove, rename, rmdir, system
from os.path    import dirname, exists, expanduser, isdir, join
from shutil     import copy, copytree, rmtree
from stat       import S_IWRITE
from sys        import argv, platform
from urllib     import urlretrieve
from zipfile    import is_zipfile, ZipFile

# from http://stackoverflow.com/questions/1889597/deleting-directory-in-python
def remove_readonly(file_name, path, _):
    """removed read-only entity"""
    if file_name is rmdir:
        chmod(path, S_IWRITE)
        rmdir(path)
    elif file_name is remove:
        chmod(path, S_IWRITE)
        remove(path)

def extractall(zipfile, path):
    """extracted all from zipfile"""
    if not exists( path ):
        makedirs( path )
    for fname in zipfile.namelist():
        local_file_name_ = join(path, fname)
        local_file_dir = dirname( local_file_name_ )
        if not exists( local_file_dir ):
            makedirs( local_file_dir )
        print 'Extracting %(0)s to %(1)s' % { '0' : fname, '1' : path }
        local_file = open( local_file_name_, 'w' )
        local_file.write( zipfile.read(fname) )
        local_file.close()

def format(format_string, *args):
    params_count = 0
    params_set = {}
    for param in args:
        format_string = format_string.replace( '{'+str(params_count)+'}', '%('+str(params_count)+')s' )
        params_set[str(params_count)] = param
        params_count = params_count+1

    return format_string % params_set

def backup_dir(dir_name, backup_dir_name):
    """ backup dir """
    if exists(backup_dir_name):
        print format('{0} already exists, remove it first!', backup_dir_name)
        exit(2)
    if exists(dir_name):
        rename(dir_name, backup_dir_name)

def get_plugin(plugin, getter, to_dir):
    """ load plugin to to_dir via getter """
    if 'url' in getter:
        if 'no_sub_dirs' in plugin:
            local_dir = to_dir
        else:
            to_dir = join(to_dir, plugin.name)
            local_dir = join(to_dir, plugin.type)
            makedirs(local_dir)
        local_file_name = join(
            local_dir, 
            format('{0}.{1}', plugin.name, plugin.ext)
        )
        print format('Downloading {0} to {1}', plugin.name, local_dir)
        urlretrieve( format(getter.url, plugin.url), local_file_name )

        if 'extract' in plugin:
            if not is_zipfile(local_file_name):
                print format('{0} is not valid zip file!', local_file_name)
            else:
                local_dir = to_dir
                if plugin.extract != '':
                    local_dir = join(local_dir, plugin.extract)
                print format('Extracting {0} to {1}', local_file_name, local_dir)
                zip_file = ZipFile(local_file_name, 'r')
                extractall(zip_file, local_dir)

    elif 'run' in getter:
        next_name = plugin.url.split('/')[-1]
        if next_name.find('.') >= 0:
            next_name = next_name.rpartition('.')[0]
        if next_name == None or next_name == '':
            print format('{0} parsing name error', plugin.url)
            exit(4)
        if 'no_sub_dirs' not in plugin:
            to_dir = join(to_dir, next_name)
            makedirs(to_dir)
        print format('Unpacking {0} to {1}', plugin.url, to_dir)
        system( format(getter.run, plugin.url, to_dir) )
        if 'remove_dir' in getter :
            rmtree( join(to_dir, getter.remove_dir), onerror=remove_readonly )
        if 'no_sub_dirs' in plugin:
            dest_dir = join(to_dir, plugin.dest)
            if exists(dest_dir):
                for file_name in listdir(dest_dir):
                    copy( join(dest_dir, file_name), to_dir )
                rmtree(dest_dir)
    else:
        print format('Unknown getter type: {0}', getter.type)

def get_vim_plugins():
    """load all vim plugins"""
    vim_dir = ''

    if platform == 'win32':
        vim_dir = expanduser("~/vimfiles")
    else:
        vim_dir = expanduser("~/.vim")

    cfg_file = file('plugins.cfg')
    config = Config(cfg_file)

    backup_set = set()

    for next_plugin in config.plugins:
        next_dir = join(vim_dir, next_plugin.dest+config.new_dir_pfx)
        if next_plugin.dest not in backup_set:
            if exists(next_dir):
                print format('{0} already exists, remove it first!', next_dir)
                exit(2)
            makedirs(next_dir)
            backup_set.add(next_plugin.dest)
        for next_getter in config.gets:
            if next_getter.type == next_plugin.get_type:
                get_plugin(next_plugin, next_getter, next_dir)
                break
        else:
            print format('Unknown plugin get type: {0}', next_plugin.get_type)
            exit(3)

    copy_local_plugins( join(vim_dir, 'bundle'+config.new_dir_pfx) )

    while len(backup_set) > 0:
        next_dir = join(vim_dir, backup_set.pop())
        next_old_dir = next_dir+config.old_dir_pfx
        if exists(next_old_dir):
            rmtree(next_old_dir, onerror=remove_readonly)
        if exists(next_dir):
            rename(next_dir, next_old_dir)
        next_new_dir = next_dir+config.new_dir_pfx
        if exists(next_new_dir):
            rename(next_new_dir, next_dir)

def copy_local_plugins( bundles_dir ):
    """ copied local plugins """
    if ( exists(argv[0]) ):
        local_dir = dirname(argv[0])
    else:
        local_dir = '.'
    local_dir = join(local_dir, 'local')
    if ( exists(local_dir) ):
        local_vim_dir = bundles_dir
        dir_names = opendir(local_dir)
        for name in dir_names:
            from_dir = join(local_dir, name)
            if ( isdir(from_dir) ):
                to_dir = join(local_vim_dir, name)
                print format('Copying local files from {0} to {1}', from_dir, to_dir)
                copytree(from_dir, to_dir)


if __name__ == "__main__":
    get_vim_plugins()
    exit(0)

# vim: ts=4 sw=4
