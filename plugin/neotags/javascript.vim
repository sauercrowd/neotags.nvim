let g:neotags#javascript#order = 'cCfmpo'

let g:neotags#javascript#c = {
            \   'group': 'javascriptClassTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate'
            \   ]
            \ }

let g:neotags#javascript#C = {
            \   'group': 'javascriptConstantTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate'
            \   ]
            \ }

let g:neotags#javascript#f = {
            \   'group': 'javascriptFunctionTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate',
            \       'javascriptConditional',
            \       'javascriptRepeat'
            \   ]
            \ }

let g:neotags#javascript#m = {
            \   'group': 'javascriptMethodTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate',
            \       'javascriptConditional',
            \       'javascriptRepeat'
            \   ]
            \ }

let g:neotags#javascript#o = {
            \   'group': 'javascriptObjectTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate',
            \       'javascriptConditional',
            \       'javascriptRepeat'
            \   ]
            \ }

let g:neotags#javascript#p = {
            \   'group': 'javascriptPropTag',
            \   'notin': [
            \       'jsx.*',
            \       'javascriptTemplate',
            \       'javascriptConditional',
            \       'javascriptRepeat'
            \   ]
            \ }

highlight def link javascriptClassTag	neotags_ClassTag
highlight def link javascriptConstantTag	neotags_ConstantTag
highlight def link javascriptFunctionTag	neotags_FunctionTag
highlight def link javascriptMethodTag	neotags_MethodTag
highlight def link javascriptObjectTag	neotags_ObjectTag
highlight def link javascriptPropTag	neotags_PreProcTag
