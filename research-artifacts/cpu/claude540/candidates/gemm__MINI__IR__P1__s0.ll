; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.ni = icmp sgt i32 %ni, 0
  br i1 %cmp.ni, label %outer.preheader, label %for.end40

outer.preheader:
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %cmp.nj = icmp sgt i32 %nj, 0
  %cmp.nk = icmp sgt i32 %nk, 0
  %ni64 = zext i32 %ni to i64
  br label %for.body

for.body:                                         ; preds = %for.inc38, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc39, %for.inc38 ]
  %Crow.offset = mul nsw i64 %i, %nj64
  %Crow = getelementptr inbounds double, ptr %C, i64 %Crow.offset
  %Arow.offset = mul nsw i64 %i, %nk64
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arow.offset

  br i1 %cmp.nj, label %scale.preheader, label %for.end

scale.preheader:
  br label %scale.body

scale.body:                                       ; preds = %scale.body, %scale.preheader
  %j0 = phi i64 [ 0, %scale.preheader ], [ %j0.inc, %scale.body ]
  %cptr0 = getelementptr inbounds double, ptr %Crow, i64 %j0
  %cval0 = load double, ptr %cptr0, align 8
  %mul0 = fmul double %cval0, %beta
  store double %mul0, ptr %cptr0, align 8
  %j0.inc = add nuw nsw i64 %j0, 1
  %cmp.scale = icmp slt i64 %j0.inc, %nj64
  br i1 %cmp.scale, label %scale.body, label %for.end

for.end:                                          ; preds = %scale.body, %for.body
  br i1 %cmp.nk, label %k.preheader, label %for.end37

k.preheader:
  br label %for.body13

for.body13:                                       ; preds = %for.end34, %k.preheader
  %k = phi i64 [ 0, %k.preheader ], [ %inc36, %for.end34 ]
  %aptr = getelementptr inbounds double, ptr %Arow, i64 %k
  %aval = load double, ptr %aptr, align 8
  %alpha_a = fmul double %alpha, %aval
  %Brow.offset = mul nsw i64 %k, %nj64
  %Brow = getelementptr inbounds double, ptr %B, i64 %Brow.offset

  br i1 %cmp.nj, label %inner.preheader, label %for.end34

inner.preheader:
  br label %for.body16

for.body16:                                       ; preds = %for.body16, %inner.preheader
  %j = phi i64 [ 0, %inner.preheader ], [ %inc33, %for.body16 ]
  %bptr = getelementptr inbounds double, ptr %Brow, i64 %j
  %bval = load double, ptr %bptr, align 8
  %mul26 = fmul double %alpha_a, %bval
  %cptr = getelementptr inbounds double, ptr %Crow, i64 %j
  %cval = load double, ptr %cptr, align 8
  %add31 = fadd double %cval, %mul26
  store double %add31, ptr %cptr, align 8
  %inc33 = add nuw nsw i64 %j, 1
  %cmp.inner = icmp slt i64 %inc33, %nj64
  br i1 %cmp.inner, label %for.body16, label %for.end34

for.end34:                                        ; preds = %for.body16, %for.body13
  %inc36 = add nuw nsw i64 %k, 1
  %cmp.k = icmp slt i64 %inc36, %nk64
  br i1 %cmp.k, label %for.body13, label %for.end37

for.end37:                                        ; preds = %for.end34, %for.end
  br label %for.inc38

for.inc38:                                        ; preds = %for.end37
  %inc39 = add nuw nsw i64 %i, 1
  %cmp.i = icmp slt i64 %inc39, %ni64
  br i1 %cmp.i, label %for.body, label %for.end40

for.end40:                                        ; preds = %for.inc38, %entry
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
