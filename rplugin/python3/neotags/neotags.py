# ============================================================================
# File:        neotags.py
# Author:      Christian Persson <c0r73x@gmail.com>
# Repository:  https://github.com/c0r73x/neotags.nvim
#              Released under the MIT license
# ============================================================================
import os
import re
import subprocess

import psutil


class Neotags(object):

    def __init__(self, vim):
        self.__vim = vim
        self.__prefix = '\C\<'
        self.__suffix = '\>'
        self.__is_running = False
        self.__initialized = False
        self.__highlights = {}

        self.__ignore = [
            '.*String.*',
            '.*Comment.*',
            'cIncluded',
            'cCppOut2',
            'cCppInElse2',
            'cCppOutIf2',
            'pythonDocTest',
            'pythonDocTest2'
        ]

    def init(self):
        if(self.__initialized):
            return

        self.__pattern = r'syntax match %s /%s\%%(%s\)%s/ containedin=ALLBUT,%s'
        self.__exists_buffer = {}

        if(self.__vim.vars['neotags_enabled']):
            evupd = ','.join(self.__vim.vars['neotags_events_update'])
            evhl = ','.join(self.__vim.vars['neotags_events_highlight'])

            self.__vim.command('autocmd %s * call NeotagsUpdate()' % evupd)
            self.__vim.command('autocmd %s * call NeotagsHighlight()' % evhl)

            if(self.__vim.vars['loaded_neotags']):
                self.highlight()

        self.__initialized = True

    def toggle(self):
        if(not self.__vim.vars['neotags_enabled']):
            self.__vim.vars['neotags_enabled'] = 1
        else:
            self.__vim.vars['neotags_enabled'] = 0

        self.update()

    def update(self):
        if(not self.__vim.vars['neotags_enabled']):
            self._clear()
            return

        if(self.__vim.vars['neotags_run_ctags']):
            self._run_ctags()

        self.highlight()

    def highlight(self):
        self.__exists_buffer = {}

        if(not self.__vim.vars['neotags_enabled']):
            self._clear()
            return

        if(not self.__vim.vars['neotags_highlight']):
            self._clear()
            return

        neotags_file = self.__vim.vars['neotags_file']
        tagfiles = self.__vim.eval('&tags').split(",")
        if neotags_file not in tagfiles:
            self.__vim.command('set tags+=%s' % neotags_file)
            tagfiles.append(neotags_file)

        files = []

        for f in tagfiles:
            f = re.sub(r';', '', f).encode('utf-8')

            if(os.path.isfile(f)):
                try:
                    files.append(f)
                except:
                    self.__vim.command(
                        'echom "Error: unable to open %s"' % f.decode('utf-8')
                    )

        if files is None:
            self.__vim.command("echom 'No tag files found!'")
            return

        groups, kinds = self._getTags(files)
        order = self._tags_order()

        if not order:
            order = kinds

        prevgroups = []

        for key in order:
            hlgroup = self._exists(key, '.group', None)
            filter = self._exists(key, '.filter.group', None)

            if hlgroup is not None and hlgroup in groups:
                prefix = self._exists(key, '.prefix', self.__prefix)
                suffix = self._exists(key, '.suffix', self.__suffix)
                notin = self._exists(key, '.notin', [])

                nohl = [n for n in prevgroups if not n == hlgroup] + notin
                self._highlight(hlgroup, groups[hlgroup], prefix, suffix, nohl)

                if(hlgroup not in prevgroups):
                    prevgroups.append(hlgroup)

            if filter is not None and filter in groups:
                prefix = self._exists(key, '.filter.prefix', self.__prefix)
                suffix = self._exists(key, '.filter.suffix', self.__suffix)
                notin = self._exists(key, '.filter.notin', [])

                nohl = [n for n in prevgroups if not n == filter] + notin
                self._highlight(filter, groups[filter], prefix, suffix, nohl)

                if(filter not in prevgroups):
                    prevgroups.append(filter)

    def _tags_order(self):
        orderlist = []
        filetypes = self.__vim.eval('&ft').lower().split('.')

        for filetype in filetypes:
            order = self._exists(filetype, '#order', None)

            if order:
                orderlist += [(filetype + '#') + s for s in list(order)]

        return orderlist

    def _kill(self, proc_pid):
        process = psutil.Process(proc_pid)
        for proc in process.children():
            proc.kill()
        process.kill()


    def _run_ctags(self):
        if(self.__is_running):
            return

        self.__is_running = True

        ctags_args = self.__vim.vars['neotags_ctags_args']

        if(self.__vim.vars['neotags_recursive']):
            ctags_args.append('-R')

        ctags_args.append('-f-')

        if(self.__vim.vars['neotags_appendpath']):
            ctags_args.append('"%s"' % self.__vim.funcs.getcwd())

        file = open(self.__vim.vars['neotags_file'], 'wb')

        try:
            proc = subprocess.Popen('%s %s' %
                (self.__vim.vars['neotags_ctags_bin'], ' '.join(ctags_args)),
                shell=True,
                stdout=file,
            )

            proc.wait(self.__vim.vars['neotags_ctags_timeout'])
        except subprocess.TimeoutExpired:
            self._kill(proc.pid)

            if self.__vim.vars['neotags_silent_timeout'] == 0:
                self.__vim.command(
                    'echom "Error: Ctags process timed out!"'
                )

        file.close()

        self.__is_running = False

    def _exists(self, kind, var, default):
        buffer = kind + var

        if buffer in self.__exists_buffer:
            return self.__exists_buffer[buffer]

        if self.__vim.funcs.exists("neotags#%s" % buffer):
            self.__exists_buffer[buffer] = self.__vim.eval(
                'neotags#%s' % buffer
            )
        else:
            self.__exists_buffer[buffer] = default

        return self.__exists_buffer[buffer]

    def _clear(self):
        for key in self.__highlights.keys():
            self.__vim.command(
                'silent! syntax clear %s' % key,
                async=True
            )

        self.__highlights = {}

    def _highlight(self, key, group, prefix, suffix, notin):
        current = []

        self.__vim.command('silent! syntax clear %s' % key)

        for i in range(0, len(group), 2048):
            current = group[i:i + 2048]

            self.__vim.command(self.__pattern % (
                key,
                prefix,
                '\|'.join(current),
                suffix,
                ','.join(self.__ignore + notin)
            ), async=True)

        self.__highlights[key] = 1

    def _parseLine(self, line, groups, kinds, to_escape, pattern):
        match = pattern.match(line)

        if(match):
            entry = {
                'name': match.group(1),
                'file': match.group(2),
                'cmd': match.group(3),
                'kind': match.group(4),
                'lang': self._ctags_to_vim(match.group(5))
            }

            kind = entry['lang'] + "#" + entry['kind']

            if kind not in kinds:
                kinds.append(kind)

            hlgroup = self._exists(kind, '.group', None)
            fstr = self._exists(kind, '.filter.pattern', None)
            filter = None

            if fstr is not None:
                filter = re.compile(r"%s" % fstr)

            if hlgroup is not None:

                cmd = entry['cmd']

                name = to_escape.sub(
                    r'\\\g<0>',
                    entry['name']
                )

                if filter is not None and filter.search(cmd):
                    fgrp = self._exists(kind, '.filter.group', None)

                    if fgrp is not None:
                        hlgroup = fgrp

                if hlgroup not in groups:
                    groups[hlgroup] = []

                if name not in groups[hlgroup]:
                    groups[hlgroup].append(name)

    def _getTags(self, files):
        filetypes = self.__vim.eval('&ft').lower().split('.')
        groups = {}
        kinds = []

        if filetypes is None:
            return groups, kinds

        to_escape = re.compile(r'[.*^$/\\~\[\]]')

        lang = '|'.join(self._vim_to_ctags(filetypes))
        pattern = re.compile(
            '^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\tlanguage:(%s)' % lang,
            re.IGNORECASE
        )

        for file in files:
            with open(file, 'r+', encoding='utf-8', errors='replace') as f:
                for line in f:
                    self._parseLine(
                        line,
                        groups,
                        kinds,
                        to_escape,
                        pattern
                    )

        return groups, kinds

    def _ctags_to_vim(self, lang):
        if lang is None:
            return 'unknown'

        if lang == 'C++':
            return 'cpp'
        elif lang == 'C#':
            return 'cs'

        return lang.lower()

    def _vim_to_ctags(self, languages):
        for i,l in enumerate(languages):
            if languages[i] == 'cpp':
                languages[i] = 'C++'
            elif languages[i] == 'cs':
                languages[i] = 'C#'

            languages[i] = re.escape(languages[i])

        return languages
