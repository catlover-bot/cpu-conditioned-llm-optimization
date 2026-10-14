; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64

  %ncmp = icmp sgt i32 %n, 0
  br i1 %ncmp, label %init.y.preheader, label %init.y.done

init.y.preheader:
  br label %init.y.body

init.y.body:
  %iv0 = phi i64 [ 0, %init.y.preheader ], [ %iv0.next, %init.y.body ]
  %yptr0 = getelementptr inbounds double, ptr %y, i64 %iv0
  store double 0.000000e+00, ptr %yptr0, align 8
  %iv0.next = add nuw nsw i64 %iv0, 1
  %iv0.cmp = icmp slt i64 %iv0.next, %n64
  br i1 %iv0.cmp, label %init.y.body, label %init.y.done

init.y.done:
  %mcmp = icmp sgt i32 %m, 0
  br i1 %mcmp, label %outer.preheader, label %for.end47

outer.preheader:
  br label %outer.body

outer.body:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.latch ]

  %tmpptr = getelementptr inbounds double, ptr %tmp, i64 %i
  store double 0.000000e+00, ptr %tmpptr, align 8

  %Arow = mul nsw i64 %i, %n64
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arow

  br i1 %ncmp, label %inner1.preheader, label %inner1.done

inner1.preheader:
  br label %inner1.body

inner1.body:
  %j1 = phi i64 [ 0, %inner1.preheader ], [ %j1.next, %inner1.body ]
  %acc1 = phi double [ 0.000000e+00, %inner1.preheader ], [ %acc1.next, %inner1.body ]

  %Aelt1 = getelementptr inbounds double, ptr %Arowptr, i64 %j1
  %Aval1 = load double, ptr %Aelt1, align 8
  %xelt = getelementptr inbounds double, ptr %x, i64 %j1
  %xval = load double, ptr %xelt, align 8
  %mul1 = fmul double %Aval1, %xval
  %acc1.next = fadd double %acc1, %mul1

  %j1.next = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %n64
  br i1 %j1.cmp, label %inner1.body, label %inner1.exit

inner1.exit:
  store double %acc1.next, ptr %tmpptr, align 8
  br label %inner1.done

inner1.done:
  %tmpval = load double, ptr %tmpptr, align 8

  br i1 %ncmp, label %inner2.preheader, label %outer.latch

inner2.preheader:
  br label %inner2.body

inner2.body:
  %j2 = phi i64 [ 0, %inner2.preheader ], [ %j2.next, %inner2.body ]

  %yelt = getelementptr inbounds double, ptr %y, i64 %j2
  %yval = load double, ptr %yelt, align 8
  %Aelt2 = getelementptr inbounds double, ptr %Arowptr, i64 %j2
  %Aval2 = load double, ptr %Aelt2, align 8
  %mul2 = fmul double %Aval2, %tmpval
  %add2 = fadd double %yval, %mul2
  store double %add2, ptr %yelt, align 8

  %j2.next = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %n64
  br i1 %j2.cmp, label %inner2.body, label %outer.latch

outer.latch:
  %i.next = add nuw nsw i64 %i, 1
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
