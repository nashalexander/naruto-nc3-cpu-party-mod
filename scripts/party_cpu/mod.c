/* NC3 USA Party Mode CPU research hooks. No emulator APIs are used here. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#include "cpu_ai.inc"
#define B(a) (*(volatile u8 *)(a))
#define H(a) (*(volatile u16 *)(a))
#define W(a) (*(volatile u32 *)(a))
extern u32 original_lobby(u32,u32,u32,u32);
extern u32 original_count(void);
extern u32 original_exchange(void *);
extern void *original_packet(u32,void *,u32);
extern void *original_slot(int, u16 *);
extern u32 original_character(u32,u32,u32,u32);
extern u32 original_technique(u32,u32,u32,u32);
extern void original_preview(u32);
extern void local_cpu_prepare(void *,u32);
extern void original_scene(u32,u32);
struct ModState {
    u32 active, cpus, old_touch, exchanges;
    u8 packets[4][64];
    u16 names[4][16];
    u32 in_character, control_slot, wait_release, character_object, characters_done;
    u32 exchange_caller;
    u32 in_technique, technique_object, in_battle, ai_ticks;
} state __attribute__((section(".modstate")));
static void reset_mode(void) {
    if (state.active) H(0x020c3488)=1;
    state.active=0; state.cpus=0; state.old_touch=0;
    state.in_character=0; state.control_slot=0; state.wait_release=0;
    state.character_object=0; state.characters_done=0;
    state.in_technique=0; state.technique_object=0; state.in_battle=0;
}
void scene_hook(u32 scene,u32 subscene) {
    if (scene==2) reset_mode(); /* returning to the main Mode Select */
    original_scene(scene,subscene);
}
static const u8 add_label[] __attribute__((aligned(4))) = {
    0x82,0x77,0x81,0x40,0x82,0x60,0x82,0x63,0x82,0x63,0x81,0x40,
    0x82,0x62,0x82,0x6f,0x82,0x74,0,0}; /* X ADD CPU, fullwidth SJIS */

u32 count_hook(void) {
    return state.active ? 1 + state.cpus : original_count();
}
void *slot_hook(int slot,u16 *length) {
    if (!state.active || slot < 1) return original_slot(slot,length);
    if (length) *length=24;
    state.names[slot][0]='C'; state.names[slot][1]='P';
    state.names[slot][2]='U'; state.names[slot][3]=' ';
    state.names[slot][4]='0'+slot;
    return state.names[slot];
}
u32 exchange_hook(void *outgoing) {
    if (!state.active) return original_exchange(outgoing);
    state.exchange_caller=(u32)__builtin_return_address(0);
    const u8 *p=outgoing;
    if (state.in_character) {
        for (u32 slot=0;slot<=state.cpus;slot++)
            for (u32 i=0;i<28;i++) state.packets[slot][i]=0;
        if (!((const u16*)p)[0] && !((const u16*)p)[1]) state.wait_release=0;
        if (!state.wait_release)
            for (u32 i=0;i<28;i++) state.packets[state.control_slot][i]=p[i];
    } else if (state.in_technique) {
        for (u32 i=0;i<28;i++) state.packets[0][i]=p[i];
        for (u32 slot=1;slot<=state.cpus;slot++) {
            for (u32 i=0;i<28;i++) state.packets[slot][i]=0;
            u32 phase=B(state.technique_object+0x0c+slot);
            /* Keep each CPU's native default techniques, then confirm them. */
            ((u16*)state.packets[slot])[0]=phase==1 ?
                ((state.exchanges&15)==0 ? 8 : 0) : phase==6 ? 0x21 : 0;
        }
    } else {
        for (u32 slot=0;slot<=state.cpus;slot++)
            for (u32 i=0;i<28;i++) state.packets[slot][i]=p[i];
        if (!W(0x020cdd60)) state.in_battle=0;
        if (state.in_battle) {
            for (u32 slot=1;slot<=state.cpus;slot++) {
                u16 *packet=(u16*)state.packets[slot];
                packet[0]=0; packet[3]=0; packet[4]=0; packet[5]=0; packet[6]=0xffff;
            }
        }
    }
    H(0x020c3488)=(1u << (1+state.cpus))-1;
    W(0x020c3494)=1;
    state.exchanges++;
    return 1;
}
void *packet_hook(u32 manager,void *buffer,u32 slot) {
    if (state.active && manager==0x020c4b20 && slot<4)
        return state.packets[slot];
    return original_packet(manager,buffer,slot);
}
u32 lobby_hook(u32 object,u32 b,u32 c,u32 d) {
    u32 phase=B(object+12);
    if (phase==0) reset_mode();
    if (phase==2) {
        u32 touch=H(0x020c3386)!=0;
        u32 row_y=78+32*state.cpus;
        u32 clicked=touch && !state.old_touch && H(0x020c3388)>52 &&
            H(0x020c3388)<204 && H(0x020c338a)>row_y && H(0x020c338a)<row_y+28;
        if (state.cpus<3 && ((H(0x020c3382)&0x400)||clicked) &&
                (state.active || original_count()==1)) {
            state.active=1; state.cpus++;
            H(0x020c3488)=(1u<<(1+state.cpus))-1;
        }
        state.old_touch=touch;
        if (state.active && (H(0x020c3382)&8)) {
            W(0x020c6264)=0; W(0x020c626c)=1+state.cpus;
            W(0x020c6274)=1;
            /* Follow the native fade/profile exchange before match settings. */
            ((void(*)(u32,u32))0x0201d344)(W(0x0206207c),0);
            ((void(*)(u32,u32))0x0201d344)(W(0x02062080),0);
            B(object+12)=5;
        }
    }
    u32 result=original_lobby(object,b,c,d);
    if (result==7) reset_mode();
    if (B(object+12)==2 && state.cpus<3) {
        W(0x020d4020)=1;
        /* Half a character of left padding keeps the label inside the box. */
        ((void(*)(u32,u32,const u8*))0x0207b18c)(60,78+32*state.cpus,add_label);
    }
    return result;
}
/* Native cursors reserve a fighter even before confirmation. Park future slots
 * on the empty grid cell and suspend their selector state until their turn. */
static u8 character_conflicts[37];
static void start_character_slot(u32 object,u32 slot) {
    const u8 *map=(const u8*)W(0x02066d84);
    const u8 *conflicts=(const u8*)W(0x02066da4);
    u32 selected=4; /* Prefer Naruto, then the first available unlocked fighter. */
    for (u32 attempt=0;attempt<37;attempt++) {
        u32 index=attempt ? attempt-1 : 4;
        u32 character=map[index], available=character<36 && B(object+0xb8+character);
        for (u32 other=0;available && other<slot;other++) {
            u32 prior=map[B(object+0x0c+other)*9+B(object+0x14+other)];
            if (prior==character || conflicts[prior]==character) available=0;
        }
        if (available) { selected=index; break; }
    }
    B(object+0x0c+slot)=selected/9;
    B(object+0x14+slot)=selected%9;
    B(object+0x10+slot)=0;
    u32 cursor=0x020ce654+slot*0x4c;
    W(cursor+0xa20)=0x38+50*(selected%3);
    W(cursor+0xa24)=0x22+46*((selected%9)/3);
    /* P1's ready screen reused the same message sprite for "Waiting...". */
    ((void(*)(u32,u32,u32,u32,u32))0x0201ed18)
        (W(0x020ce654+0xd08),0,1,0xfffffffe,1);
}
void preview_hook(u32 screen) {
    if (state.active && state.in_character) {
        const u32 ui=0x020ce654, object=state.character_object;
        for (u32 slot=state.control_slot+1;slot<=state.cpus;slot++) {
            B(ui+0x2af+slot*0x4c)=0; /* No portrait before this slot starts. */
            B(ui+0x3df+slot*0x4c)=0; /* No confirmed idle fighter yet. */
            B(ui+0xa1b+slot*0x4c)=0; /* No cursor for an unassigned slot. */
        }
        if (B(object+0x10+state.control_slot)==6)
            W(ui+0xdb0)=B(object+0x18+state.control_slot) ? 0x68 : 0x20;
    }
    original_preview(screen);
}
u32 character_hook(u32 object,u32 b,u32 c,u32 d) {
    if (!state.active) return original_character(object,b,c,d);
    if (!state.in_character || state.character_object!=object) {
        state.in_character=1; state.control_slot=0;
        state.character_object=object; state.wait_release=0;
        for (u32 slot=1;slot<=state.cpus;slot++) {
            B(object+0x0c+slot)=0;
            B(object+0x14+slot)=6; /* map[6] == empty (36). */
            B(object+0x10+slot)=0xff;
        }
    }
    u32 saved=W(0x020c6264);
    if (B(object+0x10+state.control_slot)<2) {
        /* A confirmed human leaves a waiting panel. Reopen the native grid. */
        const u32 ui=0x020ce654;
        B(ui+0xc7b)=0; B(ui+0xcc7)=0; B(ui+0xd13)=0;
        B(ui+0xd5f)=0; B(ui+0xdab)=0;
        const u8 *map=(const u8*)W(0x02066d84);
        u32 page=B(object+0x0c+state.control_slot);
        for (u32 i=0;i<9;i++) B(ui+0x6d7+i*0x4c)=map[page*9+i]!=36;
    }
    /* The native 36-entry conflict table has no empty-cell entry. Supply one
     * without touching the adjacent preview-resource table in game RAM. */
    u32 conflicts=W(0x02066da4), page_conflicts=W(0x020683c8);
    for (u32 i=0;i<36;i++) character_conflicts[i]=B(conflicts+i);
    character_conflicts[36]=0xff;
    W(0x02066da4)=(u32)character_conflicts;
    W(0x020683c8)=(u32)character_conflicts;
    W(0x020c6264)=state.control_slot;
    u32 result=original_character(object,b,c,d);
    W(0x020c6264)=saved;
    W(0x02066da4)=conflicts; W(0x020683c8)=page_conflicts;
    if (B(object+0x10+state.control_slot)==4 && state.control_slot<state.cpus) {
        state.control_slot++;
        start_character_slot(object,state.control_slot);
        B(0x020ce654+0x2af+state.control_slot*0x4c)=1;
        state.wait_release=1;
    }
    static u16 cpu_label[]={0x6282,0x6f82,0x7482,0x4081,0x5082,0};
    static const u16 p1_label[]={0x6f82,0x5082,0};
    cpu_label[4]=((0x4f+state.control_slot)<<8)|0x82;
    u32 font=W(0x020d4020); W(0x020d4020)=1;
    ((void(*)(u32,u32,const void*,u32))0x0207b100)(8,112,
            state.control_slot ? cpu_label : p1_label,0);
    W(0x020d4020)=font;
    if (result!=1) {
        state.in_character=0; state.control_slot=0; state.characters_done=(result==2);
    }
    return result;
}
void prepare_hook(void *working,void *input,void *source) {
    u8 *actor=working;
    u32 slot=actor[0x1d];
    if (!state.active || slot==0 || slot>state.cpus) {
        ((void(*)(void*,void*,void*))0x0202866c)(working,input,source);
        return;
    }
    state.in_battle=1;
    /* Select the nearest live opponent without the mission activation radius. */
    u8 **actors=(u8**)0x020cdd70;
    u32 target=0, distance=0xffffffff;
    int x=*(int*)(actor+0x4c), y=*(int*)(actor+0x50);
    for (u32 i=0;i<1+state.cpus;i++) {
        u8 *other=actors[i];
        if (i==slot || !other || *(int*)(other+0x30)<=0) continue;
        int dx=*(int*)(other+0x4c)-x, dy=*(int*)(other+0x50)-y;
        u32 d=(dx<0?-dx:dx)+(dy<0?-dy:dy);
        if (d<distance) { distance=d; target=i; }
    }
    actor[0xdc]=target;
    for (u32 i=0;i<60;i++) actor[0xdd+i]=generic_cpu_ai[i];
    local_cpu_prepare((void*)0x020cdd70,slot);
    state.ai_ticks++;
}
u32 technique_hook(u32 object,u32 b,u32 c,u32 d) {
    if (!state.active) return original_technique(object,b,c,d);
    state.in_technique=1; state.technique_object=object;
    u32 result=original_technique(object,b,c,d);
    if (result!=1) state.in_technique=0;
    return result;
}
