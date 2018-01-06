#!/usr/bin/env python3
import discord
import asyncio
import urllib.request
import json

client = discord.Client()

def make_loc(loc):
    return loc[1]

def cloogle_request(query, page):
    """Make a request to Cloogle"""
    response = urllib.request.urlopen(urllib.request.Request(
        'http://cloogle.org/api.php?' +
        urllib.parse.urlencode([('str', query), ('page', page)]),
        headers={'User-Agent': 'CloogleDiscord'})).read()
    results = json.loads(response.decode('utf-8'))
    return results

def make_article(search, result, fmt='plain'):
    """Format result"""
    module = 'Clean core'\
        if 'builtin' in result[1][0] and result[1][0]['builtin']\
        else result[1][0]['modul']
    metadata = []
    extras = result[1][1]

    if result[0] == 'FunctionResult':
        msg = extras['func']
        func, _ = msg.split(':==' if extras['kind'][0] == 'Macro' else '::', 1)
        title = func.strip() + ' in ' + module
        if 'constructor_of' in extras:
            metadata += ['Contructor of :: ' + extras['constructor_of']]
        if 'recordfield_of' in extras:
            metadata += ['Record field of :: ' + extras['recordfield_of']]
        if 'generic_derivations' in extras and \
                len(extras['generic_derivations']) > 0:
            metadata += ['Generic derivations:'] +\
                ['\t' + t.ljust(20) + ' in ' + ', '.join(map(make_loc, locs))
                    for [t,locs] in extras['generic_derivations']]
    elif result[0] == 'TypeResult':
        msg = extras['type']
        type_, _ = split_typedef(msg)
        title = ':: ' + type_ + ' in ' + module
        if 'type_instances' in extras and \
                len(extras['type_instances']) > 0:
            metadata += ['Instances:'] +\
                ['\t' + (i + ' ' + ' '.join(ts)).ljust(20) +
                    ' in ' + ', '.join(map(make_loc, locs))
                    for [i,ts,locs] in extras['type_instances']]
        if 'type_derivations' in extras and \
                len(extras['type_derivations']) > 0:
            metadata += ['Derivations:'] +\
                ['\t' + g.ljust(20) + ' in ' + ', '.join(map(make_loc, locs))
                    for [g,locs] in extras['type_derivations']]
    elif result[0] == 'ClassResult':
        cls = extras['class_name']
        funs = extras['class_funs']
        msg = 'class %s where' % cls
        for fun in funs:
            msg += '\n\t%s' % fun
        title = 'class %s in %s' % (cls, module)
        if 'class_instances' in extras and \
                len(extras['class_instances']) > 0:
            metadata += ['Instances:'] +\
                ['\t' + ' '.join(t).ljust(20) + ' in ' +
                    ', '.join(map(make_loc, locs))
                    for [t,locs] in extras['class_instances']]
    elif result[0] == 'ModuleResult':
        library = result[1][0]['library']
        title = '%s in %s' % (module, library)
        msg = 'import %s' % module

    if fmt == 'plain':
        return '//' + '-' * 70 + '\r\n' +\
            '// ' + title + ':\r\n' +\
            '\t' + msg.replace('\n', '\n\t') +\
            ''.join(['\r\n// ' + md for md in metadata]) + '\r\n' +\
            '//' + '-' * 70

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    roles = [role.name for role in message.author.roles]
    if message.content.startswith('!cloogle '):
        query = message.content[len('!cloogle '):]
        resp = cloogle_request(query, 0)
        if resp['return'] is 1:
            msg = "```Haskell\n"
            msg += make_article(query, resp['data'][0])
        else:
            msg = "```"
            msg = msg + str(resp['return']) + ': ' + resp['msg']
        msg = msg + "```"
        tmp = await client.send_message(message.channel, msg)

client.run('TOKEN')
