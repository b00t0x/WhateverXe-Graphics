"""Retain released client dependency and physical-match contracts.

The fixture is exported from each release's immutable Git tree. It is not
derived from the current package policy. This checks loading/matching metadata,
not native graphics execution or every mixed-version runtime combination.
"""
import argparse, json, plistlib, subprocess
from functools import lru_cache
from pathlib import Path
from kext_dependencies import version

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tools/fixtures/released_clients.json'
PROVIDER='org.b00t0x.AppleIntelTGLCompat'

def matches(info):
    return {value.lower() for p in info.get('IOKitPersonalities',{}).values()
            for value in p.get('IOPCIPrimaryMatch','').split()}

@lru_cache(maxsize=1)
def released():
    data=json.loads(FIXTURE.read_text())
    if data.get('schema')!=1 or not data.get('releases'):
        raise ValueError('missing released client contract corpus')
    return data['releases']

def check_released_clients(plists, component):
    current={p['CFBundleIdentifier']:p for path in plists for p in [plistlib.loads(path.read_bytes())]}
    provider=current.get(PROVIDER)
    if provider is None:raise ValueError(component+': missing released client provider')
    for release in released():
        for contract in release['contracts']:
            if component not in contract['components']:continue
            client=current.get(contract['identifier'])
            label=component+' / '+release['tag']+' / '+contract['identifier']
            if client is None:raise ValueError(label+': released client missing')
            lost=set(contract['matches'])-matches(client)
            if lost:raise ValueError(label+': lost released physical matches '+','.join(sorted(lost)))
            requested=contract['requires_provider']
            if requested and not version(provider['OSBundleCompatibleVersion'])<=version(requested)<=version(provider['CFBundleVersion']):
                raise ValueError(label+': released provider requirement outside current compatibility interval')

def export():
    def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
    releases=[]
    for tag in git('tag','--sort=version:refname').decode().splitlines():
        commit=git('rev-parse',tag+'^{commit}').decode().strip();groups={}
        for name in git('ls-tree','-r','--name-only',commit,'payloads').decode().splitlines():
            if not name.endswith('.kext/Contents/Info.plist'):continue
            info=plistlib.loads(git('show',commit+':'+name))
            physical=tuple(sorted(matches(info)))
            if not physical:continue
            key=(info['CFBundleIdentifier'],info.get('OSBundleLibraries',{}).get(PROVIDER),physical)
            groups.setdefault(key,[]).append(name.split('/')[1])
        releases.append({'tag':tag,'commit':commit,'contracts':[
            {'identifier':identifier,'requires_provider':requirement,'matches':list(physical),'components':components}
            for (identifier,requirement,physical),components in groups.items()]})
    if not releases:raise ValueError('local release history is required to export the corpus')
    FIXTURE.parent.mkdir(exist_ok=True)
    FIXTURE.write_text(json.dumps({'schema':1,'releases':releases},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export',action='store_true');args=p.parse_args()
    if args.export:export()
    else:
        policy=json.loads((ROOT/'tools/policy.json').read_text())
        common=list((ROOT/'payloads/Common').rglob('*.kext/Contents/Info.plist'))
        for system in policy['systems']:
            name=system['payload']
            check_released_clients(common+list((ROOT/'payloads'/name).rglob('*.kext/Contents/Info.plist')),name)
        print('PASS released client requirements and physical matches')
