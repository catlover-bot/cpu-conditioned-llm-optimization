; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %n.check, label %for.end94

n.check:
  %cmp.m = icmp sgt i32 %m, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %n.check
  %k = phi i32 [ 0, %n.check ], [ %inc93, %for.inc92 ]
  %k64 = sext i32 %k to i64
  br i1 %cmp.m, label %for.body.preheader, label %for.end.k0

for.body.preheader:
  ; nrm = sum over i of A[i][k]*A[i][k]
  br label %for.body8

for.body8:                                         ; preds = %for.body8, %for.body.preheader
  %i1 = phi i64 [ 0, %for.body.preheader ], [ %i1.next, %for.body8 ]
  %nrm1 = phi double [ 0.000000e+00, %for.body.preheader ], [ %add15, %for.body8 ]
  %rowA1 = mul nsw i64 %i1, %n64
  %rowoff1 = getelementptr inbounds double, ptr %A, i64 %rowA1
  %aik.ptr = getelementptr inbounds double, ptr %rowoff1, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %mul = fmul double %aik, %aik
  %add15 = fadd double %nrm1, %mul
  %i1.next = add nuw nsw i64 %i1, 1
  %cmp7 = icmp slt i64 %i1.next, %m64
  br i1 %cmp7, label %for.body8, label %for.end.loop

for.end.loop:
  br label %for.end.common

for.end.k0:
  br label %for.end.common

for.end.common:
  %nrm.final = phi double [ %add15, %for.end.loop ], [ 0.000000e+00, %for.end.k0 ]
  %call = call double @sqrt(double noundef %nrm.final) #2
  %Rkk.row = mul nsw i64 %k64, %n64
  %Rkk.rowoff = getelementptr inbounds double, ptr %R, i64 %Rkk.row
  %Rkk.ptr = getelementptr inbounds double, ptr %Rkk.rowoff, i64 %k64
  store double %call, ptr %Rkk.ptr, align 8
  br i1 %cmp.m, label %for.body22.preheader, label %for.end37

for.body22.preheader:
  br label %for.body22

for.body22:                                         ; preds = %for.body22, %for.body22.preheader
  %i2 = phi i64 [ 0, %for.body22.preheader ], [ %i2.next, %for.body22 ]
  %rowA2 = mul nsw i64 %i2, %n64
  %rowoffA2 = getelementptr inbounds double, ptr %A, i64 %rowA2
  %aik2.ptr = getelementptr inbounds double, ptr %rowoffA2, i64 %k64
  %aik2 = load double, ptr %aik2.ptr, align 8
  %div = fdiv double %aik2, %call
  %rowQ2 = mul nsw i64 %i2, %n64
  %rowoffQ2 = getelementptr inbounds double, ptr %Q, i64 %rowQ2
  %qik2.ptr = getelementptr inbounds double, ptr %rowoffQ2, i64 %k64
  store double %div, ptr %qik2.ptr, align 8
  %i2.next = add nuw nsw i64 %i2, 1
  %cmp21 = icmp slt i64 %i2.next, %m64
  br i1 %cmp21, label %for.body22, label %for.end37

for.end37:                                         ; preds = %for.body22, %for.end.common
  %k.next.i32 = add nsw i32 %k, 1
  %cmp.jn = icmp slt i32 %k.next.i32, %n
  br i1 %cmp.jn, label %for.body41.outer.preheader, label %for.end91

for.body41.outer.preheader:
  %j.start64 = sext i32 %k.next.i32 to i64
  br label %for.body41.outer

for.body41.outer:                                    ; preds = %for.inc89, %for.body41.outer.preheader
  %j64 = phi i64 [ %j.start64, %for.body41.outer.preheader ], [ %j64.next, %for.inc89 ]
  %Rkj.row = mul nsw i64 %k64, %n64
  %Rkj.rowoff = getelementptr inbounds double, ptr %R, i64 %Rkj.row
  %Rkj.ptr = getelementptr inbounds double, ptr %Rkj.rowoff, i64 %j64
  store double 0.000000e+00, ptr %Rkj.ptr, align 8
  br i1 %cmp.m, label %for.body48.preheader, label %for.end65

for.body48.preheader:
  br label %for.body48

for.body48:                                         ; preds = %for.body48, %for.body48.preheader
  %i3 = phi i64 [ 0, %for.body48.preheader ], [ %i3.next, %for.body48 ]
  %rowQ3 = mul nsw i64 %i3, %n64
  %rowoffQ3 = getelementptr inbounds double, ptr %Q, i64 %rowQ3
  %qik3.ptr = getelementptr inbounds double, ptr %rowoffQ3, i64 %k64
  %qik3 = load double, ptr %qik3.ptr, align 8
  %rowA3 = mul nsw i64 %i3, %n64
  %rowoffA3 = getelementptr inbounds double, ptr %A, i64 %rowA3
  %aij3.ptr = getelementptr inbounds double, ptr %rowoffA3, i64 %j64
  %aij3 = load double, ptr %aij3.ptr, align 8
  %mul57 = fmul double %qik3, %aij3
  %rkj3.cur = load double, ptr %Rkj.ptr, align 8
  %add62 = fadd double %rkj3.cur, %mul57
  store double %add62, ptr %Rkj.ptr, align 8
  %i3.next = add nuw nsw i64 %i3, 1
  %cmp47 = icmp slt i64 %i3.next, %m64
  br i1 %cmp47, label %for.body48, label %for.end65

for.end65:                                         ; preds = %for.body48, %for.body41.outer
  br i1 %cmp.m, label %for.body68.preheader, label %for.end88

for.body68.preheader:
  %Rkj.final = load double, ptr %Rkj.ptr, align 8
  br label %for.body68

for.body68:                                         ; preds = %for.body68, %for.body68.preheader
  %i4 = phi i64 [ 0, %for.body68.preheader ], [ %i4.next, %for.body68 ]
  %rowA4 = mul nsw i64 %i4, %n64
  %rowoffA4 = getelementptr inbounds double, ptr %A, i64 %rowA4
  %aij4.ptr = getelementptr inbounds double, ptr %rowoffA4, i64 %j64
  %aij4 = load double, ptr %aij4.ptr, align 8
  %rowQ4 = mul nsw i64 %i4, %n64
  %rowoffQ4 = getelementptr inbounds double, ptr %Q, i64 %rowQ4
  %qik4.ptr = getelementptr inbounds double, ptr %rowoffQ4, i64 %k64
  %qik4 = load double, ptr %qik4.ptr, align 8
  %mul81 = fmul double %qik4, %Rkj.final
  %sub = fsub double %aij4, %mul81
  store double %sub, ptr %aij4.ptr, align 8
  %i4.next = add nuw nsw i64 %i4, 1
  %cmp67 = icmp slt i64 %i4.next, %m64
  br i1 %cmp67, label %for.body68, label %for.end88

for.end88:                                         ; preds = %for.body68, %for.end65
  br label %for.inc89

for.inc89:                                         ; preds = %for.end88
  %j64.next = add nuw nsw i64 %j64, 1
  %j32.cur = trunc i64 %j64 to i32
  %j32.next = add nsw i32 %j32.cur, 1
  %cmp40 = icmp slt i32 %j32.next, %n
  br i1 %cmp40, label %for.body41.outer, label %for.end91

for.end91:                                         ; preds = %for.inc89, %for.end37
  br label %for.inc92

for.inc92:                                         ; preds = %for.end91
  %inc93 = add nsw i32 %k, 1
  %cmp = icmp slt i32 %inc93, %n
  br i1 %cmp, label %for.cond, label %for.end94

for.end94:                                         ; preds = %for.inc92, %entry
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
