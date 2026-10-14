; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer1.preheader, label %for.end95

outer1.preheader:                                 ; preds = %entry
  %n64 = sext i32 %n to i64
  br label %for.body.outer1

for.body.outer1:                                  ; preds = %outer1.preheader, %for.inc30
  %i1.iv = phi i64 [ 0, %outer1.preheader ], [ %i1.next, %for.inc30 ]
  %Arow1 = getelementptr inbounds double, ptr %A, i64 %i1.iv
  %rowoff1 = mul nsw i64 %i1.iv, %n64
  %Arowbase1 = getelementptr inbounds double, ptr %A, i64 %rowoff1
  %u1i.ptr = getelementptr inbounds double, ptr %u1, i64 %i1.iv
  %u1i = load double, ptr %u1i.ptr, align 8
  %u2i.ptr = getelementptr inbounds double, ptr %u2, i64 %i1.iv
  %u2i = load double, ptr %u2i.ptr, align 8
  br label %inner1

inner1:                                           ; preds = %for.body.outer1, %inner1
  %j1.iv = phi i64 [ 0, %for.body.outer1 ], [ %j1.next, %inner1 ]
  %Aij.ptr = getelementptr inbounds double, ptr %Arowbase1, i64 %j1.iv
  %Aij = load double, ptr %Aij.ptr, align 8
  %v1j.ptr = getelementptr inbounds double, ptr %v1, i64 %j1.iv
  %v1j = load double, ptr %v1j.ptr, align 8
  %mul1 = fmul double %u1i, %v1j
  %add1 = fadd double %Aij, %mul1
  %v2j.ptr = getelementptr inbounds double, ptr %v2, i64 %j1.iv
  %v2j = load double, ptr %v2j.ptr, align 8
  %mul2 = fmul double %u2i, %v2j
  %add2 = fadd double %add1, %mul2
  store double %add2, ptr %Aij.ptr, align 8
  %j1.next = add nsw i64 %j1.iv, 1
  %cmp.inner1 = icmp slt i64 %j1.next, %n64
  br i1 %cmp.inner1, label %inner1, label %for.inc30

for.inc30:                                        ; preds = %inner1
  %i1.next = add nsw i64 %i1.iv, 1
  %cmp.outer1 = icmp slt i64 %i1.next, %n64
  br i1 %cmp.outer1, label %for.body.outer1, label %for.end32

for.end32:                                        ; preds = %for.inc30
  br label %for.body.outer2

for.body.outer2:                                  ; preds = %for.end32, %for.inc55
  %i2.iv = phi i64 [ 0, %for.end32 ], [ %i2.next, %for.inc55 ]
  %xi.ptr2 = getelementptr inbounds double, ptr %x, i64 %i2.iv
  %xi.init = load double, ptr %xi.ptr2, align 8
  br label %inner2

inner2:                                           ; preds = %for.body.outer2, %inner2
  %j2.iv = phi i64 [ 0, %for.body.outer2 ], [ %j2.next, %inner2 ]
  %xacc = phi double [ %xi.init, %for.body.outer2 ], [ %xnew, %inner2 ]
  %rowoff2 = mul nsw i64 %j2.iv, %n64
  %Arowbase2 = getelementptr inbounds double, ptr %A, i64 %rowoff2
  %Aji.ptr = getelementptr inbounds double, ptr %Arowbase2, i64 %i2.iv
  %Aji = load double, ptr %Aji.ptr, align 8
  %mul45 = fmul double %beta, %Aji
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2.iv
  %yj = load double, ptr %yj.ptr, align 8
  %mul48 = fmul double %mul45, %yj
  %xnew = fadd double %xacc, %mul48
  %j2.next = add nsw i64 %j2.iv, 1
  %cmp.inner2 = icmp slt i64 %j2.next, %n64
  br i1 %cmp.inner2, label %inner2, label %for.end54

for.end54:                                        ; preds = %inner2
  store double %xnew, ptr %xi.ptr2, align 8
  br label %for.inc55

for.inc55:                                        ; preds = %for.end54
  %i2.next = add nsw i64 %i2.iv, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %n64
  br i1 %cmp.outer2, label %for.body.outer2, label %for.end57

for.end57:                                        ; preds = %for.inc55
  br label %loop3

loop3:                                            ; preds = %for.end57, %loop3
  %i3.iv = phi i64 [ 0, %for.end57 ], [ %i3.next, %loop3 ]
  %xi.ptr3 = getelementptr inbounds double, ptr %x, i64 %i3.iv
  %xi3 = load double, ptr %xi.ptr3, align 8
  %zi.ptr = getelementptr inbounds double, ptr %z, i64 %i3.iv
  %zi = load double, ptr %zi.ptr, align 8
  %add65 = fadd double %xi3, %zi
  store double %add65, ptr %xi.ptr3, align 8
  %i3.next = add nsw i64 %i3.iv, 1
  %cmp.loop3 = icmp slt i64 %i3.next, %n64
  br i1 %cmp.loop3, label %loop3, label %for.end70

for.end70:                                        ; preds = %loop3
  br label %for.body.outer4

for.body.outer4:                                  ; preds = %for.end70, %for.inc93
  %i4.iv = phi i64 [ 0, %for.end70 ], [ %i4.next, %for.inc93 ]
  %wi.ptr = getelementptr inbounds double, ptr %w, i64 %i4.iv
  %wi.init = load double, ptr %wi.ptr, align 8
  %rowoff4 = mul nsw i64 %i4.iv, %n64
  %Arowbase4 = getelementptr inbounds double, ptr %A, i64 %rowoff4
  br label %inner4

inner4:                                           ; preds = %for.body.outer4, %inner4
  %j4.iv = phi i64 [ 0, %for.body.outer4 ], [ %j4.next, %inner4 ]
  %wacc = phi double [ %wi.init, %for.body.outer4 ], [ %wnew, %inner4 ]
  %Aij4.ptr = getelementptr inbounds double, ptr %Arowbase4, i64 %j4.iv
  %Aij4 = load double, ptr %Aij4.ptr, align 8
  %mul83 = fmul double %alpha, %Aij4
  %xj.ptr = getelementptr inbounds double, ptr %x, i64 %j4.iv
  %xj = load double, ptr %xj.ptr, align 8
  %mul86 = fmul double %mul83, %xj
  %wnew = fadd double %wacc, %mul86
  %j4.next = add nsw i64 %j4.iv, 1
  %cmp.inner4 = icmp slt i64 %j4.next, %n64
  br i1 %cmp.inner4, label %inner4, label %for.end92

for.end92:                                        ; preds = %inner4
  store double %wnew, ptr %wi.ptr, align 8
  br label %for.inc93

for.inc93:                                        ; preds = %for.end92
  %i4.next = add nsw i64 %i4.iv, 1
  %cmp.outer4 = icmp slt i64 %i4.next, %n64
  br i1 %cmp.outer4, label %for.body.outer4, label %for.end95

for.end95:                                        ; preds = %for.inc93, %entry
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
