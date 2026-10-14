; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end93

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1.64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc91, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br label %for.body6.outer

for.body6.outer:                                   ; A-pass rows
  br label %row.loop.A

row.loop.A:
  %i.A = phi i64 [ 1, %for.body6.outer ], [ %i.A.next, %row.end.A ]
  %rowbase.A = mul nsw i64 %i.A, %n64
  %rowbase.Am1 = sub nsw i64 %rowbase.A, %n64
  %rowbase.Ap1 = add nsw i64 %rowbase.A, %n64
  br label %col.loop.A

col.loop.A:
  %j.A = phi i64 [ 1, %row.loop.A ], [ %j.A.next, %col.loop.A ]
  %idx.c = add nsw i64 %rowbase.A, %j.A
  %ptr.c = getelementptr inbounds double, ptr %A, i64 %idx.c
  %v.c = load double, ptr %ptr.c, align 8
  %idx.l = add nsw i64 %rowbase.A, %j.A
  %idx.lm1 = add nsw i64 %idx.l, -1
  %ptr.l = getelementptr inbounds double, ptr %A, i64 %idx.lm1
  %v.l = load double, ptr %ptr.l, align 8
  %s1 = fadd double %v.c, %v.l
  %idx.rp1 = add nsw i64 %idx.l, 1
  %ptr.r = getelementptr inbounds double, ptr %A, i64 %idx.rp1
  %v.r = load double, ptr %ptr.r, align 8
  %s2 = fadd double %s1, %v.r
  %idx.d = add nsw i64 %rowbase.Ap1, %j.A
  %ptr.d = getelementptr inbounds double, ptr %A, i64 %idx.d
  %v.d = load double, ptr %ptr.d, align 8
  %s3 = fadd double %s2, %v.d
  %idx.u = add nsw i64 %rowbase.Am1, %j.A
  %ptr.u = getelementptr inbounds double, ptr %A, i64 %idx.u
  %v.u = load double, ptr %ptr.u, align 8
  %s4 = fadd double %s3, %v.u
  %mulv = fmul double 2.000000e-01, %s4
  %ptr.B = getelementptr inbounds double, ptr %B, i64 %idx.c
  store double %mulv, ptr %ptr.B, align 8
  %j.A.next = add nsw i64 %j.A, 1
  %cmp.colA = icmp slt i64 %j.A.next, %nm1.64
  br i1 %cmp.colA, label %col.loop.A, label %row.end.A

row.end.A:
  %i.A.next = add nsw i64 %i.A, 1
  %cmp.rowA = icmp slt i64 %i.A.next, %nm1.64
  br i1 %cmp.rowA, label %row.loop.A, label %row.loop.Binit

row.loop.Binit:
  br label %row.loop.B

row.loop.B:
  %i.B = phi i64 [ 1, %row.loop.Binit ], [ %i.B.next, %row.end.B ]
  %rowbase.B = mul nsw i64 %i.B, %n64
  %rowbase.Bm1 = sub nsw i64 %rowbase.B, %n64
  %rowbase.Bp1 = add nsw i64 %rowbase.B, %n64
  br label %col.loop.B

col.loop.B:
  %j.B = phi i64 [ 1, %row.loop.B ], [ %j.B.next, %col.loop.B ]
  %bidx.c = add nsw i64 %rowbase.B, %j.B
  %bptr.c = getelementptr inbounds double, ptr %B, i64 %bidx.c
  %bv.c = load double, ptr %bptr.c, align 8
  %bidx.lm1 = add nsw i64 %bidx.c, -1
  %bptr.l = getelementptr inbounds double, ptr %B, i64 %bidx.lm1
  %bv.l = load double, ptr %bptr.l, align 8
  %bs1 = fadd double %bv.c, %bv.l
  %bidx.rp1 = add nsw i64 %bidx.c, 1
  %bptr.r = getelementptr inbounds double, ptr %B, i64 %bidx.rp1
  %bv.r = load double, ptr %bptr.r, align 8
  %bs2 = fadd double %bs1, %bv.r
  %bidx.d = add nsw i64 %rowbase.Bp1, %j.B
  %bptr.d = getelementptr inbounds double, ptr %B, i64 %bidx.d
  %bv.d = load double, ptr %bptr.d, align 8
  %bs3 = fadd double %bs2, %bv.d
  %bidx.u = add nsw i64 %rowbase.Bm1, %j.B
  %bptr.u = getelementptr inbounds double, ptr %B, i64 %bidx.u
  %bv.u = load double, ptr %bptr.u, align 8
  %bs4 = fadd double %bs3, %bv.u
  %bmulv = fmul double 2.000000e-01, %bs4
  %bptr.A = getelementptr inbounds double, ptr %A, i64 %bidx.c
  store double %bmulv, ptr %bptr.A, align 8
  %j.B.next = add nsw i64 %j.B, 1
  %cmp.colB = icmp slt i64 %j.B.next, %nm1.64
  br i1 %cmp.colB, label %col.loop.B, label %row.end.B

row.end.B:
  %i.B.next = add nsw i64 %i.B, 1
  %cmp.rowB = icmp slt i64 %i.B.next, %nm1.64
  br i1 %cmp.rowB, label %row.loop.B, label %for.inc91

for.inc91:
  %inc92 = add nsw i32 %t, 1
  %cmp.t2 = icmp slt i32 %inc92, %tsteps
  br i1 %cmp.t2, label %for.cond, label %for.end93

for.end93:
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
