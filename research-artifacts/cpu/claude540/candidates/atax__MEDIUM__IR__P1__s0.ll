; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_atax(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %x, ptr noundef %y, ptr noundef %tmp) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %init.y.preheader, label %for.end

init.y.preheader:
  %n64 = sext i32 %n to i64
  br label %init.y

init.y:
  %iv0 = phi i64 [ 0, %init.y.preheader ], [ %iv0.next, %init.y ]
  %yptr = getelementptr inbounds double, ptr %y, i64 %iv0
  store double 0.000000e+00, ptr %yptr, align 8
  %iv0.next = add nuw nsw i64 %iv0, 1
  %cmp0 = icmp slt i64 %iv0.next, %n64
  br i1 %cmp0, label %init.y, label %for.end

for.end:
  %cmp_m = icmp sgt i32 %m, 0
  br i1 %cmp_m, label %outer.preheader, label %for.end47

outer.preheader:
  %m64 = sext i32 %m to i64
  %n64.2 = sext i32 %n to i64
  br label %outer

outer:
  %i64 = phi i64 [ 0, %outer.preheader ], [ %i64.next, %inc45 ]
  %tmpptr = getelementptr inbounds double, ptr %tmp, i64 %i64
  br i1 %cmp_n, label %inner1.preheader, label %inner1.done

inner1.preheader:
  %Arowoff = mul nsw i64 %i64, %n64.2
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arowoff
  br label %inner1

inner1:
  %j64 = phi i64 [ 0, %inner1.preheader ], [ %j64.next, %inner1 ]
  %acc = phi double [ 0.000000e+00, %inner1.preheader ], [ %acc.next, %inner1 ]
  %Aelt = getelementptr inbounds double, ptr %Arowptr, i64 %j64
  %Aval = load double, ptr %Aelt, align 8
  %xelt = getelementptr inbounds double, ptr %x, i64 %j64
  %xval = load double, ptr %xelt, align 8
  %mul = fmul double %Aval, %xval
  %acc.next = fadd double %acc, %mul
  %j64.next = add nuw nsw i64 %j64, 1
  %cmp1 = icmp slt i64 %j64.next, %n64.2
  br i1 %cmp1, label %inner1, label %inner1.exit

inner1.exit:
  store double %acc.next, ptr %tmpptr, align 8
  br label %inner1.done

inner1.done:
  br i1 %cmp_n, label %inner2.preheader, label %inc45

inner2.preheader:
  %tmpval = load double, ptr %tmpptr, align 8
  %Arowoff2 = mul nsw i64 %i64, %n64.2
  %Arowptr2 = getelementptr inbounds double, ptr %A, i64 %Arowoff2
  br label %inner2

inner2:
  %j2_64 = phi i64 [ 0, %inner2.preheader ], [ %j2_64.next, %inner2 ]
  %yelt = getelementptr inbounds double, ptr %y, i64 %j2_64
  %yval = load double, ptr %yelt, align 8
  %Aelt2 = getelementptr inbounds double, ptr %Arowptr2, i64 %j2_64
  %Aval2 = load double, ptr %Aelt2, align 8
  %mul38 = fmul double %Aval2, %tmpval
  %add39 = fadd double %yval, %mul38
  store double %add39, ptr %yelt, align 8
  %j2_64.next = add nuw nsw i64 %j2_64, 1
  %cmp2 = icmp slt i64 %j2_64.next, %n64.2
  br i1 %cmp2, label %inner2, label %inc45

inc45:
  %i64.next = add nuw nsw i64 %i64, 1
  %cmp_outer = icmp slt i64 %i64.next, %m64
  br i1 %cmp_outer, label %outer, label %for.end47

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
