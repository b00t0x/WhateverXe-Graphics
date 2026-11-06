#!/usr/bin/env python3
"""Preserve released native PCI routes and GL URB corrections, without a GPU.

The frozen corpus comes from each immutable release binary, independently of
current device tables and patch emitters. Native continuation blocks are markers;
this does not exercise shader compilation, codecs, a GPU or physical output.
Requires macOS, clang and x86_64 execution (native or Rosetta).
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tools/fixtures/released_dispatch.json'
SYSTEMS = ('Big Sur', 'Monterey', 'Ventura', 'Sonoma', 'Sequoia', 'Tahoe')
# Entry and continuation offsets describe the fixed bundled donors, not host OS.
CL = {'Big Sur': (0x889f,0x8766,0x88a6), 'Monterey': (0x9568,0x9008,0x956f),
      'Ventura': (0x970d,0x937f,0x9714), 'Sonoma': (0x68ab,0x6516,0x68b2),
      'Sequoia': (0x6514,0x61c5,0x651b), 'Tahoe': (0x636f,0x6011,0x6376)}
ROUTES = [('GL', 'Common', (0x192f9f,0x19340f,0x192fa5))] + [
    (kind, system, (0x13096,0x130c1,0x1309c) if kind=='VA' else CL[system])
    for kind in ('VA','CL') for system in SYSTEMS]


def relative(kind):
    if kind == 'CL': return 'Library/GPUBundles/XeOpenCL/libCLVMIGCPlugin.dylib'
    return f'Library/GPUBundles/AppleIntelTGLGraphics{kind}Driver.bundle/Contents/MacOS/AppleIntelTGLGraphics{kind}Driver'


def build(directory):
    executable = directory / 'native-dispatch'
    subprocess.run(['clang++', '-std=c++17', '-arch', 'x86_64', '-O1',
                    str(ROOT/'tools/native_dispatch.cpp'), '-o', str(executable)], check=True)
    return executable


def routes(executable, path, kind, offsets, vendor=0x8086):
    output = subprocess.check_output([str(executable), kind, str(path),
                                     *(hex(n) for n in offsets), hex(vendor)], text=True)
    return output.split()


def urb(executable, path, inputs):
    result = {}
    for shape, quartet in enumerate(inputs):
        output=subprocess.check_output([str(executable),'urb',str(path),*quartet],text=True)
        for line in output.splitlines():
            bank, *words=line.split();assert len(words)==4
            result[f'{shape}:{bank}']=words
    assert len(result)==len(inputs)*3
    return result


def export(executable, directory, destination):
    # Use the same immutable release identities as the client-history corpus.
    releases=json.loads((ROOT/'tools/fixtures/released_clients.json').read_text())['releases']
    groups={}
    for release in releases:
        tag, commit = release['tag'], release['commit']
        for kind, system, offsets in ROUTES:
            data=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':payloads/'+system+'/'+relative(kind)])
            path=directory/'input';path.write_bytes(data)
            admitted=routes(executable,path,kind,offsets)
            assert admitted, (tag,kind,system,'empty historical route')
            if kind!='GL':
                for vendor in (0,0x1234,0xffff):
                    assert not routes(executable,path,kind,offsets,vendor), (tag,kind,system,vendor)
            corrections=None
            if kind=='GL':
                observed=urb(executable,path,SHAPES)
                corrections={str(shape):observed[f'{shape}:0'] for shape in range(4)}
                assert all(observed[f'{shape}:{bank}']==corrections[str(shape)]
                           for shape in range(4) for bank in range(3))
            key=(kind,system,tuple(admitted),json.dumps(corrections,sort_keys=True))
            record=groups.setdefault(key,dict(kind=kind,system=system,offsets=list(offsets),
                admitted=admitted,**({'urb':corrections} if corrections else {}),sources=[]))
            record['sources'].append(dict(tag=tag,sha256=hashlib.sha256(data).hexdigest()))
        print('CAPTURE',tag,flush=True)
    inventories=[]
    for contract in groups.values():
        admitted=contract.pop('admitted')
        if admitted not in inventories:inventories.append(admitted)
        contract['admission_set']=inventories.index(admitted)
    destination.write_text(json.dumps({'schema':1,
        'releases':{r['tag']:r['commit'] for r in releases},
        'admission_sets':inventories,'urb_inputs':SHAPES,
        'contracts':list(groups.values())},indent=2)+'\n')


def check(executable, fixture, payloads, package_layout=False):
    corpus=json.loads(fixture.read_text());assert corpus['schema']==1 and corpus['contracts']
    cache={};count=0
    for contract in corpus['contracts']:
        kind, system=contract['kind'],contract['system']
        path=payloads/(system.replace(' ','')+'.pkg')/'Payload'/relative(kind) if package_layout else payloads/system/relative(kind)
        key=(kind,system)
        if key not in cache:
            admitted=routes(executable,path,kind,contract['offsets'])
            if kind!='GL':
                for vendor in (0,0x1234,0xffff):
                    assert not routes(executable,path,kind,contract['offsets'],vendor), (kind,system,'foreign vendor route',vendor)
            cache[key]=(set(admitted),urb(executable,path,corpus['urb_inputs']) if kind=='GL' else None)
        admitted, corrections=cache[key]
        label='/'.join(source['tag'] for source in contract['sources'])+' / '+kind+' / '+system
        lost=set(corpus['admission_sets'][contract['admission_set']])-admitted
        assert not lost, (label,'lost released native routes',sorted(lost))
        if corrections:
            # Old passthrough layouts may gain a new correction. Preserve every
            # correction actually made by an old release, including peer words.
            for shape, expected in contract['urb'].items():
                original=corpus['urb_inputs'][int(shape)]
                if expected!=original:
                    for bank in range(3):
                        case=f'{shape}:{bank}'
                        assert corrections[case]==expected,(label,'lost URB correction',case,expected,corrections[case])
        count+=len(contract['sources'])
    print(f'PASS: {count} released binary contracts; {len(cache)} actual-entry dispatches, all 16-bit IDs, vendor rejection and historical URB corrections')


SHAPES = [
    ['0803078078300000','8000000078310000','8000000078320000','8000000078330000'],
    ['0803038078300000','4000000078310000','4000000078320000','4000000078330000'],
    ['0803058078300000','6000000078310000','6000000078320000','6000000078330000'],
    ['0800088078300000','2a00000078310000','2a00000078320000','2a03036078330000'],
]


def check_payloads(payloads, package_layout=False):
    with tempfile.TemporaryDirectory(prefix='xe-native-history-') as tmp:
        check(build(Path(tmp)),FIXTURE,payloads,package_layout)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payloads',type=Path,default=ROOT/'payloads')
    p.add_argument('--fixture',type=Path,default=FIXTURE)
    p.add_argument('--package-layout',action='store_true')
    p.add_argument('--export',action='store_true',help='explicitly regenerate the corpus from immutable release commits')
    args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='xe-native-history-') as tmp:
        directory=Path(tmp);executable=build(directory)
        if args.export:export(executable,directory,args.fixture)
        else:check(executable,args.fixture,args.payloads,args.package_layout)
