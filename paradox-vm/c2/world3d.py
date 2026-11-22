"""C2 deterministic 3-D kinematics prototype.

Coordinates and time use Decimal SI units. Collision detection uses swept
point-vs-axis-aligned-box checks along each straight movement segment.
This is a kinematic simulator, not a rigid-body or fluid-dynamics engine.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable

D0 = Decimal("0")
UNIT_TO_M = {
    "mm": Decimal("0.001"), "cm": Decimal("0.01"),
    "m": Decimal("1"), "km": Decimal("1000"),
}

def dec(v):
    try: x = Decimal(str(v))
    except (InvalidOperation, ValueError) as e: raise ValueError("value must be a finite decimal") from e
    if not x.is_finite(): raise ValueError("value must be finite")
    return x

def metres(value, unit="m"):
    if unit not in UNIT_TO_M: raise ValueError("unit must be mm, cm, m, or km")
    x=dec(value)
    return x*UNIT_TO_M[unit]

@dataclass(frozen=True)
class AABB:
    name: str
    minimum: tuple[Decimal, Decimal, Decimal]
    maximum: tuple[Decimal, Decimal, Decimal]
    @classmethod
    def from_values(cls,name,minimum,maximum):
        lo=tuple(dec(v) for v in minimum); hi=tuple(dec(v) for v in maximum)
        if len(lo)!=3 or len(hi)!=3 or any(a>=b for a,b in zip(lo,hi)):
            raise ValueError("AABB requires three axes with min < max")
        return cls(name,lo,hi)

def _segment_hits_aabb(start,end,box):
    # Slab intersection for a segment parameter t in [0,1].
    t0,t1=Decimal(0),Decimal(1)
    for i in range(3):
        delta=end[i]-start[i]
        if delta==0:
            if start[i] < box.minimum[i] or start[i] > box.maximum[i]: return False
            continue
        a=(box.minimum[i]-start[i])/delta
        b=(box.maximum[i]-start[i])/delta
        enter,leave=min(a,b),max(a,b)
        t0=max(t0,enter); t1=min(t1,leave)
        if t0>t1: return False
    return True

class World3D:
    def __init__(self, position=("0","0","0"), bounds=None, obstacles=()):
        self.position=tuple(dec(v) for v in position)
        if len(self.position)!=3: raise ValueError("position must have x,y,z")
        self.velocity=(D0,D0,D0)
        self.acceleration=(D0,D0,D0)
        self.time_s=D0
        self.bounds=None
        if bounds is not None:
            lo=tuple(dec(v) for v in bounds[0]); hi=tuple(dec(v) for v in bounds[1])
            if len(lo)!=3 or len(hi)!=3 or any(a>=b for a,b in zip(lo,hi)): raise ValueError("invalid world bounds")
            self.bounds=(lo,hi)
        self.obstacles=tuple(obstacles)
        self.events=[]
        self._check_position(self.position)

    def _check_position(self,p):
        if self.bounds and any(p[i]<self.bounds[0][i] or p[i]>self.bounds[1][i] for i in range(3)):
            raise ValueError("position outside world bounds")

    def set_kinematics(self, velocity_mps, acceleration_mps2):
        v=tuple(dec(x) for x in velocity_mps); a=tuple(dec(x) for x in acceleration_mps2)
        if len(v)!=3 or len(a)!=3: raise ValueError("velocity and acceleration need x,y,z")
        self.velocity=v; self.acceleration=a

    def step(self, dt_s):
        dt=dec(dt_s)
        if dt<=0: raise ValueError("time step must be positive")
        start=self.position
        end=tuple(start[i]+self.velocity[i]*dt+self.acceleration[i]*dt*dt/2 for i in range(3))
        new_v=tuple(self.velocity[i]+self.acceleration[i]*dt for i in range(3))
        self._check_position(end)
        for obstacle in self.obstacles:
            if _segment_hits_aabb(start,end,obstacle):
                raise ValueError("collision with obstacle: "+obstacle.name)
        event={"sequence":len(self.events)+1,"time_start_s":str(self.time_s),
               "dt_s":str(dt),"start_m":[str(x) for x in start],
               "end_m":[str(x) for x in end],"velocity_end_mps":[str(x) for x in new_v]}
        self.position=end; self.velocity=new_v; self.time_s+=dt
        self.events.append(event)
        return event

    def move(self, delta, unit="m"):
        d=tuple(metres(x,unit) for x in delta)
        if len(d)!=3: raise ValueError("delta needs x,y,z")
        start=self.position; end=tuple(start[i]+d[i] for i in range(3))
        self._check_position(end)
        for obstacle in self.obstacles:
            if _segment_hits_aabb(start,end,obstacle): raise ValueError("collision with obstacle: "+obstacle.name)
        event={"sequence":len(self.events)+1,"kind":"translation","unit_input":unit,
               "start_m":[str(x) for x in start],"delta_m":[str(x) for x in d],
               "end_m":[str(x) for x in end]}
        self.position=end; self.events.append(event); return event

    def snapshot(self):
        return {"schema":"paradox-vm-c2-state-v1","coordinate_unit":"m",
          "time_unit":"s","position_m":[str(x) for x in self.position],
          "velocity_mps":[str(x) for x in self.velocity],
          "acceleration_mps2":[str(x) for x in self.acceleration],
          "time_s":str(self.time_s),"event_count":len(self.events),"events":self.events}

def save_state(path, world):
    payload=world.snapshot()
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    envelope={"state":payload,"sha256":sha256(canonical).hexdigest()}
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(target.suffix+".tmp")
    temp.write_text(json.dumps(envelope,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    temp.replace(target)
    return envelope["sha256"]

def load_state(path):
    envelope=json.loads(Path(path).read_text(encoding="utf-8"))
    state=envelope["state"]
    canonical=json.dumps(state,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    if sha256(canonical).hexdigest()!=envelope.get("sha256"): raise ValueError("state digest mismatch")
    return state

def replay_events(initial_position, events):
    p=tuple(dec(x) for x in initial_position)
    for event in events:
        if event.get("kind")=="translation":
            start=tuple(dec(x) for x in event["start_m"])
            if p!=start: raise ValueError("event chain discontinuity")
            delta=tuple(dec(x) for x in event["delta_m"])
            p=tuple(p[i]+delta[i] for i in range(3))
            if p!=tuple(dec(x) for x in event["end_m"]): raise ValueError("event result mismatch")
        elif "dt_s" in event:
            start=tuple(dec(x) for x in event["start_m"])
            if p!=start: raise ValueError("event chain discontinuity")
            dt=dec(event["dt_s"])
            # Replay requires kinematic inputs to be stored in the event.
            if "acceleration_mps2" not in event or "velocity_start_mps" not in event:
                raise ValueError("kinematic event missing replay inputs")
            v=tuple(dec(x) for x in event["velocity_start_mps"])
            a=tuple(dec(x) for x in event["acceleration_mps2"])
            p=tuple(start[i]+v[i]*dt+a[i]*dt*dt/2 for i in range(3))
            if p!=tuple(dec(x) for x in event["end_m"]): raise ValueError("event result mismatch")
        else: raise ValueError("unknown event type")
    return tuple(str(x) for x in p)
