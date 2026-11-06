// Execute private copies of released dispatch/URB code, never load the driver.
// Only native continuation blocks become markers. Enter through the real site.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>
#include <sys/mman.h>

extern "C" unsigned runGL(void *, unsigned), runVA(void *, void *), runCL(void *, unsigned);
extern "C" uint64_t runURB(void *, void *, unsigned);
asm(".text\n"
    ".globl _runGL\n_runGL:\nmov %rdi,%rax\nmov %esi,%edx\ncall *%rax\nret\n"
    ".globl _runVA\n_runVA:\npush %rbx\nmov %rsi,%rbx\ncall *%rdi\npop %rbx\nret\n"
    ".globl _runCL\n_runCL:\npush %rbp\nmov %rsp,%rbp\n"
    "push %rbx\npush %r12\npush %r13\npush %r14\nsub $0x200,%rsp\n"
    "mov %rdi,%r11\nmov %esi,%eax\nmov %esi,-0x1e8(%rbp)\n"
    "lea -0x1f0(%rbp),%r13\nmov %r13,%r14\ncall *%r11\n"
    "add $0x200,%rsp\npop %r14\npop %r13\npop %r12\npop %rbx\npop %rbp\nret\n"
    ".globl _runURB\n_runURB:\npush %rbx\npush %r15\nmov %edx,%ebx\n"
    "lea -0x3978(%rsi),%r15\nmovabs $0x123456789abcdef0,%rdx\ncall *%rdi\n"
    "mov %rdx,%rax\npop %r15\npop %rbx\nret\n");

static uint8_t *load(const char *path, size_t &size) {
    std::ifstream f(path, std::ios::binary);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)), {});
    assert(data.size() >= 32);
    uint32_t magic, cpu;
    memcpy(&magic, data.data(), 4); memcpy(&cpu, data.data()+4, 4);
    assert(magic == 0xfeedfacf && cpu == 0x1000007);
    size = data.size();
    auto p = static_cast<uint8_t *>(mmap(nullptr, size, 7, MAP_PRIVATE|MAP_ANON, -1, 0));
    assert(p != MAP_FAILED); memcpy(p, data.data(), size); return p;
}

static void marker(uint8_t *p, size_t size, unsigned offset, unsigned value) {
    assert(offset + 6 <= size);
    const uint8_t code[] = {0xb8, uint8_t(value), 0, 0, 0, 0xc3};
    memcpy(p+offset, code, sizeof(code));
}

static unsigned number(const char *s) {
    char *end; auto n = strtoul(s, &end, 0); assert(*s && !*end && n <= UINT32_MAX);
    return unsigned(n);
}

int main(int argc, char **argv) {
    assert(argc == 7);
    size_t size; auto p = load(argv[2], size);
    if (!strcmp(argv[1], "urb")) {
        assert(size > 0xa0c2);
        p[0xa0c2] = 0xc3;
        uint64_t words[4];
        for (unsigned i=0; i<4; ++i) {
            char *end; words[i]=strtoull(argv[3+i], &end, 16); assert(*argv[3+i] && !*end);
        }
        for (unsigned bank=0; bank<3; ++bank) {
            std::vector<uint8_t> state(4*0xa70+64, 0xa5);
            for (unsigned j=0; j<4; ++j) memcpy(state.data()+j*0xa70+bank*8, words+j, 8);
            auto untouched = state;
            assert(runURB(p+0xa0b8, state.data(), bank) == 0x123456789abcdef0ULL);
            printf("%u", bank);
            for (unsigned j=0; j<4; ++j) {
                uint64_t word; memcpy(&word, state.data()+j*0xa70+bank*8, 8);
                printf(" %016llx", (unsigned long long)word);
                memcpy(untouched.data()+j*0xa70+bank*8, &word, 8);
            }
            puts(""); assert(state == untouched); // Every other byte must survive.
        }
    } else {
        assert(argc == 7);
        unsigned entry=number(argv[3]), yes=number(argv[4]), no=number(argv[5]);
        unsigned vendor=number(argv[6]); assert(entry<size && vendor<=0xffff);
        marker(p, size, yes, 1); marker(p, size, no, 0);
        std::vector<uint8_t> object(0xa880); bool first=true;
        for (unsigned device=0; device<65536; ++device) {
            const unsigned identity=(device<<16)|vendor;
            memcpy(object.data()+0xa878, &identity, 4);
            unsigned result;
            if (!strcmp(argv[1], "GL")) result=runGL(p+entry, device);
            else if (!strcmp(argv[1], "VA")) result=runVA(p+entry, object.data());
            else { assert(!strcmp(argv[1], "CL")); result=runCL(p+entry, identity); }
            assert(result<=1);
            if (result) { printf("%s%04x", first?"":" ", device); first=false; }
        }
        puts("");
    }
    assert(munmap(p,size)==0);
}
