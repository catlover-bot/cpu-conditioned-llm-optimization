; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_correlation(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %corr, ptr noundef %mean, ptr noundef %stddev) #0 {
entry:
  %eps = fadd double 0.000000e+00, 1.000000e-01
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  %mgt0 = icmp sgt i32 %m, 0
  br i1 %mgt0, label %loop1.preheader, label %for.end20

loop1.preheader:
  %ngt0 = icmp sgt i32 %n, 0
  br label %loop1.j

loop1.j:
  %j1 = phi i64 [ 0, %loop1.preheader ], [ %j1.next, %loop1.j.end ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ngt0, label %loop1.i.preheader, label %loop1.j.end

loop1.i.preheader:
  br label %loop1.i

loop1.i:
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.next, %loop1.i ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.preheader ], [ %sum1.next, %loop1.i ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %rowptr1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %dptr1 = getelementptr inbounds double, ptr %rowptr1, i64 %j1
  %dval1 = load double, ptr %dptr1, align 8
  %sum1.next = fadd double %sum1, %dval1
  %i1.next = add nsw i64 %i1, 1
  %cmp1i = icmp slt i64 %i1.next, %n64
  br i1 %cmp1i, label %loop1.i, label %loop1.i.exit

loop1.i.exit:
  %divres1 = fdiv double %sum1.next, %float_n
  store double %divres1, ptr %mean.j.ptr, align 8
  br label %loop1.j.end

loop1.j.end:
  store double 0.000000e+00, ptr %mean.j.ptr, align 8, !dbg !16
  br label %dummy_unused

dummy_unused:
  unreachable
}

; Placeholder attribute group retained to satisfy declarations elsewhere (unused).
attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
