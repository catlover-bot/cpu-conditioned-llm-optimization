; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp0 = icmp sgt i32 %n, 0
  br i1 %cmp0, label %preheader, label %for.end95

preheader:
  %n64 = sext i32 %n to i64

  br label %loop1.outer

loop1.outer:                                      ; preds = %preheader, %loop1.outer.inc
  %i1 = phi i64 [ 0, %preheader ], [ %i1.next, %loop1.outer.inc ]
  %Arow1 = getelementptr inbounds double, ptr %A, i64 %i1
  %u1i.gep = getelementptr inbounds double, ptr %u1, i64 %i1
  %u1i = load double, ptr %u1i.gep, align 8
  %u2i.gep = getelementptr inbounds double, ptr %u2, i64 %i1
  %u2i = load double, ptr %u2i.gep, align 8
  %rowoff1 = mul nsw i64 %i1, %n64
  %rowptr1 = getelementptr inbounds double, ptr %A, i64 %rowoff1
  br label %loop1.inner

loop1.inner:                                      ; preds = %loop1.outer, %loop1.inner
  %j1 = phi i64 [ 0, %loop1.outer ], [ %j1.next, %loop1.inner ]
  %Aij.gep = getelementptr inbounds double, ptr %rowptr1, i64 %j1
  %Aij = load double, ptr %Aij.gep, align 8
  %v1j.gep = getelementptr inbounds double, ptr %v1, i64 %j1
  %v1j = load double, ptr %v1j.gep, align 8
  %m1 = fmul double %u1i, %v1j
  %a1 = fadd double %Aij, %m1
  %v2j.gep = getelementptr inbounds double, ptr %v2, i64 %j1
  %v2j = load double, ptr %v2j.gep, align 8
  %m2 = fmul double %u2i, %v2j
  %a2 = fadd double %a1, %m2
  store double %a2, ptr %Aij.gep, align 8
  %j1.next = add nsw i64 %j1, 1
  %cmp1inner = icmp slt i64 %j1.next, %n64
  br i1 %cmp1inner, label %loop1.inner, label %loop1.outer.inc

loop1.outer.inc:                                  ; preds = %loop1.inner
  %i1.next = add nsw i64 %i1, 1
  %cmp1outer = icmp slt i64 %i1.next, %n64
  br i1 %cmp1outer, label %loop1.outer, label %loop2.outer.entry

loop2.outer.entry:
  br label %loop2.outer

loop2.outer:                                      ; preds = %loop2.outer.entry, %loop2.outer.inc
  %i2 = phi i64 [ 0, %loop2.outer.entry ], [ %i2.next, %loop2.outer.inc ]
  %xi2.gep = getelementptr inbounds double, ptr %x, i64 %i2
  %xi2.init = load double, ptr %xi2.gep, align 8
  br label %loop2.inner

loop2.inner:                                      ; preds = %loop2.outer, %loop2.inner
  %j2 = phi i64 [ 0, %loop2.outer ], [ %j2.next, %loop2.inner ]
  %xacc = phi double [ %xi2.init, %loop2.outer ], [ %add49, %loop2.inner ]
  %rowoff2 = mul nsw i64 %j2, %n64
  %Aji.gep = getelementptr inbounds double, ptr %A, i64 %rowoff2
  %Aji.gep2 = getelementptr inbounds double, ptr %Aji.gep, i64 %i2
  %Aji = load double, ptr %Aji.gep2, align 8
  %mul45 = fmul double %beta, %Aji
  %yj.gep = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.gep, align 8
  %mul48 = fmul double %mul45, %yj
  %add49 = fadd double %xacc, %mul48
  %j2.next = add nsw i64 %j2, 1
  %cmp2inner = icmp slt i64 %j2.next, %n64
  br i1 %cmp2inner, label %loop2.inner, label %loop2.end

loop2.end:                                        ; preds = %loop2.inner
  store double %add49, ptr %xi2.gep, align 8
  br label %loop2.outer.inc

loop2.outer.inc:                                  ; preds = %loop2.end
  %i2.next = add nsw i64 %i2, 1
  %cmp2outer = icmp slt i64 %i2.next, %n64
  br i1 %cmp2outer, label %loop2.outer, label %loop3.entry

loop3.entry:
  br label %loop3

loop3:                                             ; preds = %loop3.entry, %loop3
  %i3 = phi i64 [ 0, %loop3.entry ], [ %i3.next, %loop3 ]
  %xi3.gep = getelementptr inbounds double, ptr %x, i64 %i3
  %xi3 = load double, ptr %xi3.gep, align 8
  %zi3.gep = getelementptr inbounds double, ptr %z, i64 %i3
  %zi3 = load double, ptr %zi3.gep, align 8
  %add65 = fadd double %xi3, %zi3
  store double %add65, ptr %xi3.gep, align 8
  %i3.next = add nsw i64 %i3, 1
  %cmp3 = icmp slt i64 %i3.next, %n64
  br i1 %cmp3, label %loop3, label %loop4.entry

loop4.entry:
  br label %loop4.outer

loop4.outer:                                       ; preds = %loop4.entry, %loop4.outer.inc
  %i4 = phi i64 [ 0, %loop4.entry ], [ %i4.next, %loop4.outer.inc ]
  %wi4.gep = getelementptr inbounds double, ptr %w, i64 %i4
  %wi4.init = load double, ptr %wi4.gep, align 8
  %rowoff4 = mul nsw i64 %i4, %n64
  %rowptr4 = getelementptr inbounds double, ptr %A, i64 %rowoff4
  br label %loop4.inner

loop4.inner:                                       ; preds = %loop4.outer, %loop4.inner
  %j4 = phi i64 [ 0, %loop4.outer ], [ %j4.next, %loop4.inner ]
  %wacc = phi double [ %wi4.init, %loop4.outer ], [ %add87, %loop4.inner ]
  %Aij4.gep = getelementptr inbounds double, ptr %rowptr4, i64 %j4
  %Aij4 = load double, ptr %Aij4.gep, align 8
  %mul83 = fmul double %alpha, %Aij4
  %xj4.gep = getelementptr inbounds double, ptr %x, i64 %j4
  %xj4 = load double, ptr %xj4.gep, align 8
  %mul86 = fmul double %mul83, %xj4
  %add87 = fadd double %wacc, %mul86
  %j4.next = add nsw i64 %j4, 1
  %cmp4inner = icmp slt i64 %j4.next, %n64
  br i1 %cmp4inner, label %loop4.inner, label %loop4.end

loop4.end:                                         ; preds = %loop4.inner
  store double %add87, ptr %wi4.gep, align 8
  br label %loop4.outer.inc

loop4.outer.inc:                                   ; preds = %loop4.end
  %i4.next = add nsw i64 %i4, 1
  %cmp4outer = icmp slt i64 %i4.next, %n64
  br i1 %cmp4outer, label %loop4.outer, label %for.end95

for.end95:                                         ; preds = %loop4.outer.inc, %entry
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
