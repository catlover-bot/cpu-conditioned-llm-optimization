; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1.64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc215, %preheader
  %t = phi i32 [ 1, %preheader ], [ %inc216, %for.inc215 ]
  br label %for.body.i.1

for.body.i.1:
  br label %outer.i.header

outer.i.header:
  %i = phi i64 [ 1, %for.body.i.1 ], [ %i.next, %outer.i.latch ]
  %i.add1 = add nuw nsw i64 %i, 1
  %i.sub1 = add nsw i64 %i, -1
  %ibase.A = mul nuw i64 %i, %n64
  %ibase.A = mul nuw i64 %ibase.A, %n64
  %ibase.A.p1 = mul nuw i64 %i.add1, %n64
  %ibase.A.p1 = mul nuw i64 %ibase.A.p1, %n64
  %ibase.A.m1 = mul nsw i64 %i.sub1, %n64
  %ibase.A.m1 = mul nsw i64 %ibase.A.m1, %n64
  br label %outer.j.header

outer.j.header:
  %j = phi i64 [ 1, %outer.i.header ], [ %j.next, %outer.j.latch ]
  %j.add1 = add nuw nsw i64 %j, 1
  %j.sub1 = add nsw i64 %j, -1
  %jbase = mul nsw i64 %j, %n64
  %jbase.p1 = mul nsw i64 %j.add1, %n64
  %jbase.m1 = mul nsw i64 %j.sub1, %n64

  %rowc = add nsw i64 %ibase.A, %jbase
  %rowip1 = add nsw i64 %ibase.A.p1, %jbase
  %rowim1 = add nsw i64 %ibase.A.m1, %jbase
  %rowjp1 = add nsw i64 %ibase.A, %jbase.p1
  %rowjm1 = add nsw i64 %ibase.A, %jbase.m1

  %ptrc = getelementptr inbounds double, ptr %A, i64 %rowc
  %ptrip1 = getelementptr inbounds double, ptr %A, i64 %rowip1
  %ptrim1 = getelementptr inbounds double, ptr %A, i64 %rowim1
  %ptrjp1 = getelementptr inbounds double, ptr %A, i64 %rowjp1
  %ptrjm1 = getelementptr inbounds double, ptr %A, i64 %rowjm1

  %Browc = add nsw i64 %ibase.A, %jbase
  %Bptrc = getelementptr inbounds double, ptr %B, i64 %Browc

  br label %for.body16

for.body16:                                       ; preds = %for.cond13, %outer.j.header
  %k = phi i64 [ 1, %outer.j.header ], [ %k.next, %for.body16 ]

  %a.c = getelementptr inbounds double, ptr %ptrc, i64 %k
  %a.ip1 = getelementptr inbounds double, ptr %ptrip1, i64 %k
  %a.im1 = getelementptr inbounds double, ptr %ptrim1, i64 %k
  %a.jp1 = getelementptr inbounds double, ptr %ptrjp1, i64 %k
  %a.jm1 = getelementptr inbounds double, ptr %ptrjm1, i64 %k
  %kp1 = add nuw nsw i64 %k, 1
  %km1 = add nsw i64 %k, -1
  %a.kp1 = getelementptr inbounds double, ptr %ptrc, i64 %kp1
  %a.km1 = getelementptr inbounds double, ptr %ptrc, i64 %km1

  %v.ip1 = load double, ptr %a.ip1, align 8
  %v.c = load double, ptr %a.c, align 8
  %mul.a1 = fmul double 2.000000e+00, %v.c
  %sub.a1 = fsub double %v.ip1, %mul.a1
  %v.im1 = load double, ptr %a.im1, align 8
  %add.a1 = fadd double %sub.a1, %v.im1
  %mul.b1 = fmul double 1.250000e-01, %add.a1

  %v.jp1 = load double, ptr %a.jp1, align 8
  %v.c2 = load double, ptr %a.c, align 8
  %mul.a2 = fmul double 2.000000e+00, %v.c2
  %sub.a2 = fsub double %v.jp1, %mul.a2
  %v.jm1 = load double, ptr %a.jm1, align 8
  %add.a2 = fadd double %sub.a2, %v.jm1
  %mul.b2 = fmul double 1.250000e-01, %add.a2

  %sum1 = fadd double %mul.b1, %mul.b2

  %v.kp1 = load double, ptr %a.kp1, align 8
  %v.c3 = load double, ptr %a.c, align 8
  %mul.a3 = fmul double 2.000000e+00, %v.c3
  %sub.a3 = fsub double %v.kp1, %mul.a3
  %v.km1 = load double, ptr %a.km1, align 8
  %add.a3 = fadd double %sub.a3, %v.km1
  %mul.b3 = fmul double 1.250000e-01, %add.a3

  %sum2 = fadd double %sum1, %mul.b3

  %v.c4 = load double, ptr %a.c, align 8
  %result = fadd double %sum2, %v.c4

  %b.c = getelementptr inbounds double, ptr %Bptrc, i64 %k
  store double %result, ptr %b.c, align 8

  %k.next = add nuw nsw i64 %k, 1
  %kcmp = icmp slt i64 %k.next, %nm1.64
  br i1 %kcmp, label %for.body16, label %for.end

for.end:                                          ; preds = %for.body16
  br label %outer.j.latch

outer.j.latch:
  %j.next = add nuw nsw i64 %j, 1
  %jcmp = icmp slt i64 %j.next, %nm1.64
  br i1 %jcmp, label %outer.j.header, label %for.end103

for.end103:                                       ; preds = %outer.j.latch
  br label %outer.i.latch

outer.i.latch:
  %i.next = add nuw nsw i64 %i, 1
  %icmp = icmp slt i64 %i.next, %nm1.64
  br i1 %icmp, label %outer.i.header, label %for.end106

for.end106:                                       ; preds = %outer.i.latch
  br label %outer2.i.header

outer2.i.header:
  %ii = phi i64 [ 1, %for.end106 ], [ %ii.next, %outer2.i.latch ]
  %ii.add1 = add nuw nsw i64 %ii, 1
  %ii.sub1 = add nsw i64 %ii, -1
  %iibase.B = mul nuw i64 %ii, %n64
  %iibase.B = mul nuw i64 %iibase.B, %n64
  %iibase.B.p1 = mul nuw i64 %ii.add1, %n64
  %iibase.B.p1 = mul nuw i64 %iibase.B.p1, %n64
  %iibase.B.m1 = mul nsw i64 %ii.sub1, %n64
  %iibase.B.m1 = mul nsw i64 %iibase.B.m1, %n64
  br label %outer2.j.header

outer2.j.header:
  %jj = phi i64 [ 1, %outer2.i.header ], [ %jj.next, %outer2.j.latch ]
  %jj.add1 = add nuw nsw i64 %jj, 1
  %jj.sub1 = add nsw i64 %jj, -1
  %jjbase = mul nsw i64 %jj, %n64
  %jjbase.p1 = mul nsw i64 %jj.add1, %n64
  %jjbase.m1 = mul nsw i64 %jj.sub1, %n64

  %Browc = add nsw i64 %iibase.B, %jjbase
  %Browip1 = add nsw i64 %iibase.B.p1, %jjbase
  %Browim1 = add nsw i64 %iibase.B.m1, %jjbase
  %Browjp1 = add nsw i64 %iibase.B, %jjbase.p1
  %Browjm1 = add nsw i64 %iibase.B, %jjbase.m1

  %Bptrc2 = getelementptr inbounds double, ptr %B, i64 %Browc
  %Bptrip1 = getelementptr inbounds double, ptr %B, i64 %Browip1
  %Bptrim1 = getelementptr inbounds double, ptr %B, i64 %Browim1
  %Bptrjp1 = getelementptr inbounds double, ptr %B, i64 %Browjp1
  %Bptrjm1 = getelementptr inbounds double, ptr %B, i64 %Browjm1

  %Arowc = add nsw i64 %iibase.B, %jjbase
  %Aptrc2 = getelementptr inbounds double, ptr %A, i64 %Arowc

  br label %for.body118

for.body118:                                      ; preds = %for.cond115, %outer2.j.header
  %kk = phi i64 [ 1, %outer2.j.header ], [ %kk.next, %for.body118 ]

  %b.c2 = getelementptr inbounds double, ptr %Bptrc2, i64 %kk
  %b.ip1 = getelementptr inbounds double, ptr %Bptrip1, i64 %kk
  %b.im1 = getelementptr inbounds double, ptr %Bptrim1, i64 %kk
  %b.jp1 = getelementptr inbounds double, ptr %Bptrjp1, i64 %kk
  %b.jm1 = getelementptr inbounds double, ptr %Bptrjm1, i64 %kk
  %kkp1 = add nuw nsw i64 %kk, 1
  %kkm1 = add nsw i64 %kk, -1
  %b.kp1 = getelementptr inbounds double, ptr %Bptrc2, i64 %kkp1
  %b.km1 = getelementptr inbounds double, ptr %Bptrc2, i64 %kkm1

  %w.ip1 = load double, ptr %b.ip1, align 8
  %w.c = load double, ptr %b.c2, align 8
  %wmul.a1 = fmul double 2.000000e+00, %w.c
  %wsub.a1 = fsub double %w.ip1, %wmul.a1
  %w.im1 = load double, ptr %b.im1, align 8
  %wadd.a1 = fadd double %wsub.a1, %w.im1
  %wmul.b1 = fmul double 1.250000e-01, %wadd.a1

  %w.jp1 = load double, ptr %b.jp1, align 8
  %w.c2 = load double, ptr %b.c2, align 8
  %wmul.a2 = fmul double 2.000000e+00, %w.c2
  %wsub.a2 = fsub double %w.jp1, %wmul.a2
  %w.jm1 = load double, ptr %b.jm1, align 8
  %wadd.a2 = fadd double %wsub.a2, %w.jm1
  %wmul.b2 = fmul double 1.250000e-01, %wadd.a2

  %wsum1 = fadd double %wmul.b1, %wmul.b2

  %w.kp1 = load double, ptr %b.kp1, align 8
  %w.c3 = load double, ptr %b.c2, align 8
  %wmul.a3 = fmul double 2.000000e+00, %w.c3
  %wsub.a3 = fsub double %w.kp1, %wmul.a3
  %w.km1 = load double, ptr %b.km1, align 8
  %wadd.a3 = fadd double %wsub.a3, %w.km1
  %wmul.b3 = fmul double 1.250000e-01, %wadd.a3

  %wsum2 = fadd double %wsum1, %wmul.b3

  %w.c4 = load double, ptr %b.c2, align 8
  %wresult = fadd double %wsum2, %w.c4

  %a.c2 = getelementptr inbounds double, ptr %Aptrc2, i64 %kk
  store double %wresult, ptr %a.c2, align 8

  %kk.next = add nuw nsw i64 %kk, 1
  %kkcmp = icmp slt i64 %kk.next, %nm1.64
  br i1 %kkcmp, label %for.body118, label %for.end208

for.end208:                                       ; preds = %for.body118
  br label %outer2.j.latch

outer2.j.latch:
  %jj.next = add nuw nsw i64 %jj, 1
  %jjcmp = icmp slt i64 %jj.next, %nm1.64
  br i1 %jjcmp, label %outer2.j.header, label %for.end211

for.end211:                                       ; preds = %outer2.j.latch
  br label %outer2.i.latch

outer2.i.latch:
  %ii.next = add nuw nsw i64 %ii, 1
  %iicmp = icmp slt i64 %ii.next, %nm1.64
  br i1 %iicmp, label %outer2.i.header, label %for.end214

for.end214:                                       ; preds = %outer2.i.latch
  br label %for.inc215

for.inc215:                                       ; preds = %for.end214
  %inc216 = add nsw i32 %t, 1
  %tcmp = icmp sle i32 %inc216, 100
  br i1 %tcmp, label %for.cond, label %for.end217

for.end217:                                       ; preds = %for.inc215, %entry
  ret void
}

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
