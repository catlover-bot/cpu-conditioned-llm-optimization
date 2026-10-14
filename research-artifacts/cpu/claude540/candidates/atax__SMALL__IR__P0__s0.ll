; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %y.init.preheader, label %for.end

y.init.preheader:
  %n64 = sext i32 %n to i64
  br label %y.init.body

y.init.body:
  %yi = phi i64 [0, %y.init.preheader], [%yi.next, %y.init.body]
  %y.gep = getelementptr inbounds double, ptr %y, i64 %yi
  store double 0.000000e+00, ptr %y.gep, align 8
  %yi.next = add nsw i64 %yi, 1
  %yi.cmp = icmp slt i64 %yi.next, %n64
  br i1 %yi.cmp, label %y.init.body, label %for.end

for.end:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end47

outer.preheader:
  %n64b = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %outer.body

outer.body:
  %i = phi i64 [0, %outer.preheader], [%i.next, %outer.latch]
  %tmp.gep = getelementptr inbounds double, ptr %tmp, i64 %i
  ; compute row base pointer of A for row i
  %rowoff = mul nsw i64 %i, %n64b
  %rowbase = getelementptr inbounds double, ptr %A, i64 %rowoff

  br i1 %cmp.n, label %inner1.preheader, label %inner1.done

inner1.preheader:
  br label %inner1.body

inner1.body:
  %j1 = phi i64 [0, %inner1.preheader], [%j1.next, %inner1.body]
  %acc = phi double [0.000000e+00, %inner1.preheader], [%acc.next, %inner1.body]
  %Aij.gep = getelementptr inbounds double, ptr %rowbase, i64 %j1
  %Aij = load double, ptr %Aij.gep, align 8
  %xj.gep = getelementptr inbounds double, ptr %x, i64 %j1
  %xj = load double, ptr %xj.gep, align 8
  %mul1 = fmul double %Aij, %xj
  %acc.next = fadd double %acc, %mul1
  %j1.next = add nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %n64b
  br i1 %j1.cmp, label %inner1.body, label %inner1.exit

inner1.exit:
  %acc.final = phi double [%acc.next, %inner1.body]
  br label %inner1.done

inner1.done:
  %tmp.val = phi double [0.000000e+00, %outer.body], [%acc.final, %inner1.exit]
  store double %tmp.val, ptr %tmp.gep, align 8

  br i1 %cmp.n, label %inner2.preheader, label %outer.latch

inner2.preheader:
  br label %inner2.body

inner2.body:
  %j2 = phi i64 [0, %inner2.preheader], [%j2.next, %inner2.body]
  %Aij2.gep = getelementptr inbounds double, ptr %rowbase, i64 %j2
  %Aij2 = load double, ptr %Aij2.gep, align 8
  %ygep = getelementptr inbounds double, ptr %y, i64 %j2
  %yold = load double, ptr %ygep, align 8
  %mul2 = fmul double %Aij2, %tmp.val
  %add2 = fadd double %yold, %mul2
  store double %add2, ptr %ygep, align 8
  %j2.next = add nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %n64b
  br i1 %j2.cmp, label %inner2.body, label %outer.latch

outer.latch:
  %i.next = add nsw i64 %i, 1
  %i.cmp = icmp slt i64 %i.next, %m64
  br i1 %i.cmp, label %outer.body, label %for.end47

for.end47:
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
