"""T39 adversarial composition experiment."""
import hashlib, json, random, threading
from dataclasses import dataclass
import pytest

VIOLATIONS=[f"V{i}" for i in range(1,15)]

@dataclass
class State:
    epoch:int=1
    revoked:bool=False
    trusted:bool=True
    available:bool=True
    granted:set=None
    consumed:set=None
    def __post_init__(self):
        self.granted=set() if self.granted is None else self.granted
        self.consumed=set() if self.consumed is None else self.consumed

class Authority:
    def __init__(self):
        self.lock=threading.Lock(); self.s=State()
    def invalidate(self,v):
        with self.lock:
            if v in {"V4","V5","V13","V14"}: self.s.epoch+=1
            if v=="V8": self.s.revoked=True
            if v=="V7": self.s.trusted=False
            if v=="V10": self.s.available=False
    def grant(self,b):
        with self.lock:
            if not self.s.available: raise PermissionError
            if self.s.revoked or not self.s.trusted: raise PermissionError
            if b in self.s.granted: raise PermissionError
            self.s.granted.add(b); return self.s.epoch
    def consume(self,b,epoch):
        with self.lock:
            if b in self.s.consumed: return False
            if not self.s.available or self.s.revoked or not self.s.trusted: return False
            if epoch!=self.s.epoch: return False
            self.s.consumed.add(b); return True

def binding():
    a={"agent":"t39-agent","execution":"e39","call":"c39","tool":"test.effect","args":{"value":39},"policy":"t39-policy"}
    return hashlib.sha256(json.dumps(a,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def evaluate(vs):
    a=Authority(); b=binding()
    for v in ("V7","V8","V10"):
        if v in vs: a.invalidate(v)
    if "V13" in vs:
        try: a.grant(b)
        except PermissionError: return False,False
        a.invalidate("V13"); return False,False
    if "V1" in vs or "V3" in vs or "V5" in vs or "V6" in vs or "V9" in vs: return False,False
    try: epoch=a.grant(b)
    except PermissionError: return False,False
    if "V2" in vs: return False,False
    if "V12" in vs:
        a.invalidate("V12"); return False,False
    if "V14" in vs or "V4" in vs: a.invalidate("V14" if "V14" in vs else "V4")
    if "V11" in vs:
        out=[a.consume(b,epoch),a.consume(b,epoch)]
        return sum(out)==1,sum(out)==1
    first=a.consume(b,epoch); second=a.consume(b,epoch)
    return first or second, first or second

@pytest.mark.parametrize("vs",[
 {"V2","V3"},{"V4","V6"},{"V7","V4"},{"V8","V4"},{"V5","V6"},
 {"V12","V4","V8"},{"V14","V5","V8"},{"V2","V4","V5"},{"V3","V8","V11"}])
def test_t39_hand_selected(vs):
    assert evaluate(vs)==(False,False)

def test_t39_valid_control():
    assert evaluate(set())==(True,True)

def test_t39_property_based_random():
    rng=random.Random(39039); seen=set()
    for _ in range(250):
        vs=set(rng.sample(VIOLATIONS,rng.randint(2,5))); seen.add(tuple(sorted(vs)))
        assert evaluate(vs)==(False,False), sorted(vs)
    assert len(seen)>=50

def test_t39_recovery_after_adversarial_sequence():
    for vs in [{"V2","V3"},{"V4","V8"},{"V12","V14","V5"}]:
        assert evaluate(vs)==(False,False)
    assert evaluate(set())==(True,True)

def test_t39_concurrent_dual_consume():
    a=Authority(); b=binding(); epoch=a.grant(b); results=[]; bar=threading.Barrier(2)
    def worker():
        bar.wait(); results.append(a.consume(b,epoch))
    ts=[threading.Thread(target=worker) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sum(results)==1
