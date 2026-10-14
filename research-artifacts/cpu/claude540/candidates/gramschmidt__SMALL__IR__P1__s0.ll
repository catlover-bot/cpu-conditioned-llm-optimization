; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.mn = icmp sgt i32 %m, 0
  %cmp.nn = icmp sgt i32 %n, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.k

for.k:
  %k = phi i32 [ 0, %entry ], [ %k.next, %for.k.end ]
  %k.cmp = icmp slt i32 %k, %n
  br i1 %k.cmp, label %for.k.body, label %for.end94

for.k.body:
  br i1 %cmp.mn, label %nrm.loop.ph, label %nrm.done

nrm.loop.ph:
  %k64 = sext i32 %k to i64
  br label %nrm.loop

nrm.loop:
  %i.nrm = phi i64 [ 0, %nrm.loop.ph ], [ %i.nrm.next, %nrm.loop ]
  %nrm.acc = phi double [ 0.000000e+00, %nrm.loop.ph ], [ %nrm.next, %nrm.loop ]
  %rowoff.nrm = mul nsw i64 %i.nrm, %n64
  %elemidx.nrm = add nsw i64 %rowoff.nrm, %k64
  %aptr.nrm = getelementptr inbounds double, ptr %A, i64 %elemidx.nrm
  %aval.nrm = load double, ptr %aptr.nrm, align 8
  %mul.nrm = fmul double %aval.nrm, %aval.nrm
  %nrm.next = fadd double %nrm.acc, %mul.nrm
  %i.nrm.next = add nuw nsw i64 %i.nrm, 1
  %nrm.cmp = icmp slt i64 %i.nrm.next, %m64
  br i1 %nrm.cmp, label %nrm.loop, label %nrm.done

nrm.done:
  %nrm.final = phi double [ 0.000000e+00, %for.k.body ], [ %nrm.next, %nrm.loop ]
  %k64.2 = sext i32 %k to i64
  %sqrt.call = call double @sqrt(double noundef %nrm.final) #2
  %rdiag.off = mul nsw i64 %k64.2, %n64
  %rdiag.idx = add nsw i64 %rdiag.off, %k64.2
  %rdiag.ptr = getelementptr inbounds double, ptr %R, i64 %rdiag.idx
  store double %sqrt.call, ptr %rdiag.ptr, align 8

  br i1 %cmp.mn, label %qk.loop.ph, label %qk.done

qk.loop.ph:
  br label %qk.loop

qk.loop:
  %i.qk = phi i64 [ 0, %qk.loop.ph ], [ %i.qk.next, %qk.loop ]
  %rowoff.qk = mul nsw i64 %i.qk, %n64
  %aidx.qk = add nsw i64 %rowoff.qk, %k64.2
  %aptr.qk = getelementptr inbounds double, ptr %A, i64 %aidx.qk
  %aval.qk = load double, ptr %aptr.qk, align 8
  %div.qk = fdiv double %aval.qk, %sqrt.call
  %qrowoff.qk = mul nsw i64 %i.qk, %n64
  %qidx.qk = add nsw i64 %qrowoff.qk, %k64.2
  %qptr.qk = getelementptr inbounds double, ptr %Q, i64 %qidx.qk
  store double %div.qk, ptr %qptr.qk, align 8
  %i.qk.next = add nuw nsw i64 %i.qk, 1
  %qk.cmp = icmp slt i64 %i.qk.next, %m64
  br i1 %qk.cmp, label %qk.loop, label %qk.done

qk.done:
  %j.start = add nsw i32 %k, 1
  br label %for.j

for.j:
  %j = phi i32 [ %j.start, %qk.done ], [ %j.next, %for.j.end ]
  %j.cmp = icmp slt i32 %j, %n
  br i1 %j.cmp, label %for.j.body, label %for.end91

for.j.body:
  %j64 = sext i32 %j to i64
  %rzero.off = mul nsw i64 %k64.2, %n64
  %rzero.idx = add nsw i64 %rzero.off, %j64
  %rzero.ptr = getelementptr inbounds double, ptr %R, i64 %rzero.idx
  store double 0.000000e+00, ptr %rzero.ptr, align 8

  br i1 %cmp.mn, label %racc.loop.ph, label %racc.done

racc.loop.ph:
  br label %racc.loop

racc.loop:
  %i.ra = phi i64 [ 0, %racc.loop.ph ], [ %i.ra.next, %racc.loop ]
  %qrow.ra = mul nsw i64 %i.ra, %n64
  %qidx.ra = add nsw i64 %qrow.ra, %k64.2
  %qptr.ra = getelementptr inbounds double, ptr %Q, i64 %qidx.ra
  %qval.ra = load double, ptr %qptr.ra, align 8
  %arow.ra = mul nsw i64 %i.ra, %n64
  %aidx.ra = add nsw i64 %arow.ra, %j64
  %aptr.ra = getelementptr inbounds double, ptr %A, i64 %aidx.ra
  %aval.ra = load double, ptr %aptr.ra, align 8
  %mul.ra = fmul double %qval.ra, %aval.ra
  %rptr.ra = getelementptr inbounds double, ptr %R, i64 %rzero.idx
  %rcur.ra = load double, ptr %rptr.ra, align 8
  %radd.ra = fadd double %rcur.ra, %mul.ra
  store double %radd.ra, ptr %rptr.ra, align 8
  %i.ra.next = add nuw nsw i64 %i.ra, 1
  %ra.cmp = icmp slt i64 %i.ra.next, %m64
  br i1 %ra.cmp, label %racc.loop, label %racc.done

racc.done:
  br i1 %cmp.mn, label %sub.loop.ph, label %sub.done

sub.loop.ph:
  %rfinal.ptr = getelementptr inbounds double, ptr %R, i64 %rzero.idx
  %rfinal.val = load double, ptr %rfinal.ptr, align 8
  br label %sub.loop

sub.loop:
  %i.sub = phi i64 [ 0, %sub.loop.ph ], [ %i.sub.next, %sub.loop ]
  %arow.sub = mul nsw i64 %i.sub, %n64
  %aidx.sub = add nsw i64 %arow.sub, %j64
  %aptr.sub = getelementptr inbounds double, ptr %A, i64 %aidx.sub
  %aval.sub = load double, ptr %aptr.sub, align 8
  %qrow.sub = mul nsw i64 %i.sub, %n64
  %qidx.sub = add nsw i64 %qrow.sub, %k64.2
  %qptr.sub = getelementptr inbounds double, ptr %Q, i64 %qidx.sub
  %qval.sub = load double, ptr %qptr.sub, align 8
  %mul.sub = fmul double %qval.sub, %rfinal.val
  %subres = fsub double %aval.sub, %mul.sub
  store double %subres, ptr %aptr.sub, align 8
  %i.sub.next = add nuw nsw i64 %i.sub, 1
  %sub.cmp = icmp slt i64 %i.sub.next, %m64
  br i1 %sub.cmp, label %sub.loop, label %sub.done

sub.done:
  br label %for.j.end

for.j.end:
  %j.next = add nsw i32 %j, 1
  br label %for.j

for.end91:
  br label %for.k.end

for.k.end:
  %k.next = add nsw i32 %k, 1
  br label %for.k

for.end94:
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
